class Action:
    def __init__(self):
        self.text = ""
        self.action_choice = -1 # -1: cannot parse; -2: out of range

action_list = ["", "move up", "move down", "move left", "move right",
            "move forward (away from the camera)", "move backward (towards the camera)"]
options_string = "\n".join([f"{i}. {option}" for i, option in enumerate(
    action_list) if i > 0])  # remove the first idle option
    