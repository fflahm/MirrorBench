import os
from PIL import Image
import json
import time
import argparse
from agent import AgentAPI, AgentRandom
from prompts import PROMPTS
from preprocess import construct
from action import action_list, options_string

instruction_dict = {
    "Human": "You are playing the role of a simulated human agent performing a self-recognition task inside a 3D virtual environment.",
    "Robot": "You are playing the role of a simulated robotic agent performing a self-recognition task inside a 3D virtual environment.",
}

parser = argparse.ArgumentParser()
parser.add_argument("--body", type=str)
parser.add_argument("--hand", type=str)
parser.add_argument("--mark", type=str)
parser.add_argument("--level", type=int, help="MSR level: 0, 1, 2, or 3")
parser.add_argument("--model", type=str, help="Model name to use")
parser.add_argument("--max_steps", type=int, default=-1, help="Maximum number of steps, -1 for auto")
parser.add_argument("--max_image_history", type=int, default=1, help="Maximum number of images to keep in history")
parser.add_argument("--headless", action="store_true", help="Run in headless mode")
args = parser.parse_args()

def get_feedback(feedback):
    return "execution without collisions" if feedback else "unsuccessful execution (due to collisions)"

# Prepare args
body = args.body
hand = args.hand
mark = args.mark
level = args.level
if level not in [0, 1, 2, 3]:
    raise ValueError("Level must be 0, 1, 2, or 3")
model = args.model
tag = time.strftime("%Y%m%d-%H%M%S")

result_dir = os.path.join("results", f"level{level}", model, f"{body}-{hand}-{mark}")
os.makedirs(result_dir, exist_ok=True)
result_file = os.path.join(result_dir, f"{tag}.json")

log_dir = os.path.join("logs", tag)
os.makedirs(log_dir, exist_ok=False)
log_file = os.path.join(log_dir, "logs_env.txt")
log_file_agent = os.path.join(log_dir, "logs_agent.txt")
obs_dir = os.path.join(log_dir, "obs")
os.makedirs(obs_dir, exist_ok=False)
args_file = os.path.join(log_dir, "args.json")

task_dict = construct({"body": body, "hand": hand, "mark": mark})
if task_dict["body"]["track"] != task_dict["hand"]["track"]:
    raise ValueError("Track mismatch!")
track = task_dict["body"]["track"]

# Initialize environment
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": args.headless})  # Start APP in headless or non-headless mode
from env import MirrorEnv
env = MirrorEnv(simulation_app, task_dict)
obs, feedback, dist, accomplish = env.reset()
Image.fromarray(obs).save(os.path.join(obs_dir, "0.png"))
max_steps = int(dist / env.step_size) + 10 if args.max_steps < 0 else args.max_steps
max_image_history = args.max_image_history

# Initialize agent
if model == "random":
    agent = AgentRandom(log_file=log_file_agent)
else:
    agent = AgentAPI(model=model, log_file=log_file_agent)
with open(args_file, "w") as f:
    json.dump({
        "track": track,
        "body": body,
        "hand": hand,
        "mark": mark,
        "level": level,
        "model": model,
        "max_steps": max_steps,
        "max_image_history": max_image_history
    }, f, indent=4)

prompt_prefix = PROMPTS[level][0].format(task=instruction_dict[track] ,body_full=task_dict["body"]["desc_full"],
        body=task_dict["body"]["desc_short"], hand=task_dict["hand"]["desc"], 
        mark=task_dict["mark"]["desc"], images=max_image_history)
prompt_suffix = PROMPTS[level][1].format(options=options_string, steps=max_steps, 
                                         body=task_dict["body"]["desc_short"],
                                         mark=task_dict["mark"]["desc"], images=max_image_history)

agent.start(prompt_prefix, prompt_suffix, max_steps, max_image_history)

dists = [dist]
bad_response_count = 0
for i in range(1, agent.max_steps + 1):
    print(f"Step {i} for {model} {body}-{hand}-{mark} at level {level}, tag {tag}: Distance to goal: {dist:.4f}")
    action = agent.act(
        obs, get_feedback(feedback), action_list)
    with open(log_file, "a") as f:
        f.write(f"Step {i}:\n")
        f.write(f"Action Text:\n\n{action.text}\n")
        f.write(f"Action Number: {action.action_choice}\n")
    if action.action_choice > 0 and action.action_choice < len(action_list):
        obs, feedback, dist, accomplish = env.step(action)
        Image.fromarray(obs).save(os.path.join(obs_dir, f"{i}_{action_list[action.action_choice]}.png"))
        dists.append(dist)
        with open(log_file, "a") as f:
            f.write(f"Action Choice: {action_list[action.action_choice]}\n")
            f.write(f"Distance: {dist:.4f}, Feedback:{feedback}, Accomplish:{accomplish}\n\n")
    else:
        bad_response_count += 1
        dists.append(dists[-1])
        with open(log_file, "a") as f:
            f.write("Model bad response.\n\n")
    if accomplish:
        break

with open(result_file, "w") as f:
    json.dump({
        "track": track,
        "tag": tag,
        "steps": len(dists[1:]),
        "task_success": accomplish, # 
        "improvement_steps": sum(b < a - 1e-5 for a, b in zip(dists, dists[1:])),
        "sir": sum(b < a - 1e-5 for a, b in zip(dists, dists[1:])) / len(dists[1:]),
        "fcr": 1 - (dists[-1]-env.dist_thresh) / (dists[0]-env.dist_thresh),
        "pcr": 1 - (min(dists)-env.dist_thresh) / (dists[0]-env.dist_thresh),
        "bad_response": bad_response_count,
        "distances": dists
    }, f, indent=4)
env.close()