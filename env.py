import numpy as np
import os
# Isaac Sim core API (4.5)
from isaacsim.core.api import World
from isaacsim.core.api.objects import FixedCuboid
from isaacsim.core.prims import XFormPrim
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.utils.viewports import set_camera_view
from isaacsim.sensors.camera import Camera
import isaacsim.core.utils.numpy.rotations as rot_utils
from pxr import UsdGeom, UsdShade, Sdf, Gf, UsdPhysics, PhysxSchema
from isaacsim.storage.native import get_assets_root_path
import carb

root_dict = {"none": "",
              "local": "A:/isaac-sim-assets-1-4.5.0/Assets/Isaac/4.5",
              "remote": get_assets_root_path(),
              "this": os.getcwd()}

class MirrorEnv:
    def __init__(self, sim_app, task_dict):
        # Initilize world
        self.sim_app = sim_app
        self.world = World(stage_units_in_meters=1.0)
        self.stage = self.world.stage

        # Define parameters
        self.step_size = 0.1
        self.dist_thresh = self.step_size + 1e-5

        self.mirror_scale = np.array([0.01, 2.0, 2.0])
        self.mirror_pos = np.array([2.0, 0.0, self.mirror_scale[2]/2])
        self.mirror_collison_x = self.mirror_scale[0]
      
        self.body_usd_path = root_dict[task_dict["body"]["root"]] + task_dict["body"]["path"]
        self.body_pos = np.array((task_dict["body"]["pos"])) if "pos" in task_dict["body"] else np.array([0.0, 0.0, 0.0])
        self.body_ori = np.array((task_dict["body"]["ori"])) if "ori" in task_dict["body"] else np.array([0.0, 0.0, 90.0])
        self.body_scale = np.array((task_dict["body"]["scale"])) if "scale" in task_dict["body"] else 1.0
        self.body_collision_x = task_dict["body"]["collision_x"]

        self.hand_usd_path = root_dict[task_dict["hand"]["root"]] + task_dict["hand"]["path"]
        self.hand_pos_init = np.array((task_dict["body"]["hand_pos_init"]))
        self.hand_ori = np.array((task_dict["hand"]["ori"])) if "ori" in task_dict["hand"] else np.array([0.0, 0.0, 0.0])
        self.hand_scale = np.array((task_dict["hand"]["scale"])) if "scale" in task_dict["hand"] else 1.0
        self.hand_collison_x = task_dict["hand"]["collision_x"]
        self.hand_color = task_dict["hand"]["color"]

        self.mark_texture_path = task_dict["mark"]["path"]
        self.mark_pos = np.array((task_dict["body"]["mark_pos"]))
        self.mark_pos[0] = self.body_pos[0] + self.body_collision_x / 2  # align with body
        self.mark_scale = 0.2 * task_dict["mark"]["scale"] if "scale" in task_dict["mark"] else 0.2

        self.camera_focal = task_dict["body"]["camera_focal"] if "camera_focal" in task_dict["body"] else 3.0

        self.goal_pos = self.mark_pos + np.array([self.hand_collison_x / 2, 0.0, 0.0])

        if not self._check_goal_valid():
            raise ValueError("Initial goal position is not valid. Please adjust the positions.")
        
        # Create environment
        self._create_background()
        self._create_body()
        self._create_mark()
        self._create_hand()
        self._create_mirror()
        self._create_camera()

    def _create_background(self):
        env_prim_path = "/World/SimpleRoom"
        env_usd_path = os.path.join(os.getcwd(), "assets", "Simple_Room", "simple_room.usd")
        add_reference_to_stage(usd_path=env_usd_path, prim_path=env_prim_path)

    def _create_body(self):
        body_prim_path = "/World/Body"
        add_reference_to_stage(usd_path=self.body_usd_path, prim_path=body_prim_path)
        self._disable_physics(body_prim_path)
        body = XFormPrim(prim_paths_expr=body_prim_path)
        body.set_world_poses(positions=np.array([self.body_pos]), orientations=rot_utils.euler_angles_to_quats(np.array([self.body_ori]), degrees=True, extrinsic=False))
        body.set_local_scales(scales=np.array([[self.body_scale, self.body_scale, self.body_scale]]))

    def _create_mark(self):
        if self.mark_texture_path is None:
            return
        mark_prim_path = "/World/Mark"
        mark_usd_path = "./assets/uv_cube.usdc"  
        add_reference_to_stage(usd_path=mark_usd_path, prim_path=mark_prim_path)
        mark_prim = UsdGeom.Xformable(self.world.stage.GetPrimAtPath(mark_prim_path))
        mark_prim.AddTranslateOp().Set(Gf.Vec3d(*self.mark_pos))
        mark_prim.AddRotateXYZOp().Set(Gf.Vec3d(-90.0, 0.0, 0.0))
        mark_prim.AddScaleOp().Set(Gf.Vec3d(1.0, self.mark_scale, self.mark_scale))
        self._create_and_bind_material(prim_path=mark_prim_path, 
                                       mat_path="/World/Looks/MarkMaterial",
                                       texture_path=self.mark_texture_path)
        
    def _create_hand(self):
        hand_prim_path = "/World/Hand"
        add_reference_to_stage(usd_path=self.hand_usd_path, prim_path=hand_prim_path)
        self._disable_physics(hand_prim_path)

        self.hand = XFormPrim(prim_paths_expr=hand_prim_path)
        self.hand.set_world_poses(positions=np.array([self.hand_pos_init]),
                                  orientations=rot_utils.euler_angles_to_quats(np.array([self.hand_ori]), 
                                    degrees=True, extrinsic=False))
        self.hand.set_local_scales(scales=np.array([[self.hand_scale, self.hand_scale, self.hand_scale]]))
        if not self.hand_color is None:
            self._create_and_bind_material(prim_path=hand_prim_path, 
                                        mat_path="/World/Looks/HandMaterial", 
                                        color=[c / 255.0 for c in self.hand_color], 
                                        metallic=0.0, 
                                        roughness=0.5)
                
    def _create_mirror(self):
        FixedCuboid(
            prim_path="/World/Mirror",
            name="mirror",
            position=self.mirror_pos,
            size=1.0,
            scale=self.mirror_scale
        )
        self._create_and_bind_material(prim_path="/World/Mirror", 
                                       mat_path="/World/Looks/MirrorMaterial", 
                                       color=[0.95, 0.95, 0.95], 
                                       metallic=1.0, 
                                       roughness=0.0)

    def _create_camera(self):
        self.camera = Camera(
            prim_path="/World/Camera",
            translation=np.array([-0.8, -0.3, 0.9]),
            frequency=20,
            resolution=(1024, 1024)
        )
        set_camera_view(eye=[-1.1, 0.0, 2.0], target=[0.0, 0.0, 1.7], camera_prim_path="/World/Camera")
        self.camera.set_focal_length(self.camera_focal)

    def _create_and_bind_material(self, prim_path, mat_path, color=[1.0, 1.0, 1.0], metallic=1.0, roughness=0.0, texture_path=None):     
        prim = self.stage.GetPrimAtPath(prim_path)
        if not prim or not prim.IsValid():
            raise RuntimeError(f"Prim {prim_path} not found to bind material.")

        mat_path = Sdf.Path(mat_path)
        mat = UsdShade.Material.Define(self.stage, mat_path)
        shader = UsdShade.Shader.Define(self.stage, mat_path.AppendChild("PreviewSurface"))
        shader.CreateIdAttr("UsdPreviewSurface")

        if texture_path is not None:
            tex = UsdShade.Shader.Define(self.stage, mat_path.AppendChild("Tex"))
            tex.CreateIdAttr("UsdUVTexture")
            tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(texture_path))
            tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
            primvar = UsdShade.Shader.Define(self.stage, mat_path.AppendChild("Primvar"))
            primvar.CreateIdAttr("UsdPrimvarReader_float2")
            primvar.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
            primvar.CreateOutput("result", Sdf.ValueTypeNames.Float2)
            tex.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
                primvar.ConnectableAPI(), "result"
            )
            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
                tex.ConnectableAPI(), "rgb"
            )
        else:
            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
            shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
            shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
        mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        UsdShade.MaterialBindingAPI(prim).Bind(mat)

    def _disable_physics(self, prim_path):
        for sub_prim in self.stage.Traverse():
            if str(sub_prim.GetPath()).startswith(prim_path):
                if sub_prim.HasAPI(UsdPhysics.RigidBodyAPI):
                    sub_prim.RemoveAPI(UsdPhysics.RigidBodyAPI)
                if sub_prim.HasAPI(UsdPhysics.CollisionAPI):
                    sub_prim.RemoveAPI(UsdPhysics.CollisionAPI)
                if sub_prim.HasAPI(PhysxSchema.PhysxRigidBodyAPI):
                    sub_prim.RemoveAPI(PhysxSchema.PhysxRigidBodyAPI)
                if sub_prim.HasAPI(PhysxSchema.PhysxCollisionAPI):
                    sub_prim.RemoveAPI(PhysxSchema.PhysxCollisionAPI)

    def reset(self):
        self.world.reset()
        self.camera.initialize()
        for _ in range(50):
            self.world.step(render=True)
        return self.camera.get_rgb(), True, self._manhattan_distance(self.hand.get_world_poses()[0][0], self.goal_pos), False

    def _check_collision_free(self, target_pos, tol=1e-5):
        collision_free = target_pos[0] - self.hand_collison_x/2 > self.body_pos[0] + self.body_collision_x/2 - tol
        collision_free = collision_free and (target_pos[0] + self.hand_collison_x/2 < self.mirror_pos[0] - self.mirror_collison_x/2 + tol)
        return bool(collision_free)
    
    def _check_goal_valid(self, tol=1e-5):
        # Collision free & Reachable with integer steps
        goal_valid = self._check_collision_free(self.goal_pos)
        for i in range(3):
            ratio = (self.goal_pos[i] - self.hand_pos_init[i]) / self.step_size
            goal_valid = goal_valid and abs(ratio - round(ratio)) < tol
        return goal_valid

    def _manhattan_distance(self, pos_a, pos_b):
        return float(np.sum(np.abs(pos_a - pos_b)))

    def step(self, action, step_size=0.1, n_steps=50):
        curr_pos, _ = self.hand.get_world_poses()
        curr_pos = curr_pos[0] # [3,]
        choice = action.action_choice
        action_list = [None, 
                       np.array([0.0, 0.0, step_size]),   # move up
                       np.array([0.0, 0.0, -step_size]),  # move down
                       np.array([0.0, step_size, 0.0]),  # move left
                       np.array([0.0, -step_size, 0.0]), # move right
                       np.array([step_size, 0.0, 0.0]),  # move forward
                       np.array([-step_size, 0.0, 0.0]), # move backward
                       ]
        if choice < 1 or choice >= len(action_list):
            carb.log_warn(f"Invalid action {choice}. No movement.")
            action_legal = False
        else:
            target_pos = curr_pos + action_list[choice]
            action_legal = self._check_collision_free(target_pos)
            if action_legal:
                self.hand.set_world_poses(positions=np.array([target_pos]))

        for _ in range(n_steps):
            self.world.step(render=True)

        # distance = np.linalg.norm(self.hand.get_world_poses()[0][0] - self.goal_pos)
        distance = self._manhattan_distance(self.hand.get_world_poses()[0][0], self.goal_pos)
        if action_legal and distance <= self.dist_thresh:
            task_accomplished = True
        else:
            task_accomplished = False
        rgb = self.camera.get_rgb() # [H, W, 3] 0-255
        return rgb, action_legal, distance, task_accomplished
    
    def step_wait(self, n_steps=10000):
        for _ in range(n_steps):
            self.world.step(render=True)

    def close(self):
        self.sim_app.close()