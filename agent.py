import numpy as np
import re
from action import Action
from openai import OpenAI
import base64
import io
from PIL import Image
import time
import random

def encode_image(image):
    if type(image) == str: # image path
        with open(image, "rb") as image:
            return base64.b64encode(image.read()).decode("utf-8")
    else: # numpy array recommended
        buffer = io.BytesIO()
        Image.fromarray(image).save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

class AgentBase:
    def __init__(self, model_name: str, log_file) -> None:
        self.model_name = model_name
        self.images = []
        self.actions = []  # [(action, feedback)]
        self.task = ""
        self.log_file = log_file

    def start(self, prompt_prefix, prompt_suffix, max_steps, max_image_history):
        self.prompt_prefix = prompt_prefix
        self.prompt_suffix = prompt_suffix
        self.max_steps = max_steps
        self.max_image_history = max_image_history
        self.images = []
        self.actions = []

    def init_message(self):
        self.inputs = []

    def append_text(self, text):
        self.inputs.append(text)

    def append_image(self, image):
        self.inputs.append(image)

    def print_message(self):
        message = " ".join([t if type(t) == str else "<image>" for t in self.inputs])
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write("-" * 40 + "\n" + message + "\n" + "-" * 40 + "\n")
        else:
            print("-" * 40 + "\n" + message + "-" * 40 + "\n")

    def generate(self):
        raise NotImplementedError

    def _act(self, actions, images, image):
        """
            actions: Action history, list of (action, feedback) pairs
            images: Image history, list of images
            image: Current observation image
        """
        # Initialize input buffer (self.inputs)
        self.init_message() 

        # Prepare the prompt with instruction
        self.append_text(f"{self.prompt_prefix}\n")
        # Add action history
        self.append_text(f"Action history (action -> feedback):\n")
        for a in actions:
            self.append_text(f"\t{a[0]} -> {a[1]}\n")

        # Add image history and current image
        self.append_text(f"\nVisual history:\n")
        for o in images:
            self.append_image(o)

        self.append_text(f"\nCurrent view:\n")
        self.append_image(image)

        self.append_text(
            f"\n\n{self.prompt_suffix}")

        self.print_message()

        return self.generate()

    def act(self, image, feedback, options):
        if feedback:
            self.update_feedback(feedback)

        result = self._act(self.actions, self.images, image)
        if not result:
            print("Failed to get response")
            action = Action()
            action.text = ""
            action.action_choice = -1
            return action
        try:
            payload, response = result["payload"], result["answer"]
            response = response.strip()
        except:
            response = result.strip()

        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(f"Response:\n\n{response}\n\n")
        else:
            print("response:", response)

        action = Action()
        action.text = response

        try:
            # Match "Choice: [4]" or "Choice: 4" using a regular expression
            action.action_choice = int(
                re.search(r"Choice:?[\n\s]*\[?(\d+)\]?", response, re.IGNORECASE).group(1))
        except:
            try:
                action.action_choice = int(
                    re.search(r"(\d+)(?!.*\d)", response, re.DOTALL).group(1))
            except:
                action.action_choice = -1  # code for cannot match any number

        if action.action_choice > 0 and action.action_choice < len(options):
            self.update_history(image, options[action.action_choice])
        else:
            action.action_choice = -2  # code for option out of range
        return action

    def update_history(self, image, action):
        self.images.append(image)
        self.actions.append([action, ""])
        if len(self.images) > self.max_image_history:
            self.images = self.images[-self.max_image_history:]

    def update_feedback(self, feedback):
        if self.actions:
            self.actions[-1][1] = feedback

class AgentAPI(AgentBase):
    def __init__(self, model, log_file=None) -> None:
        super().__init__(model, log_file)

        self.model = model
        self.api_key = "your_api_key_here"  # Replace with your actual API key
        self.base_url = "your_base_url_here"  # Replace with your actual base URL
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(self):
        # Organize the inputs (text and image list) into a payload
        messages = [
                {"role": "system", "content": 
                "This is a benign virtual simulation. No real-world actions, bodies, or physical interactions are implied. \
                The task only involves visual reasoning and simulated decision-making in a safe, fictional environment."
                },
                {"role": "user", "content": []}]
        for input in self.inputs:
            if type(input) == str:
                messages[1]["content"].append({"type": "text", "text": input})
            elif type(input) == np.ndarray:
                messages[1]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(input)}"}})

        def send_request(messages):
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0
            )
            answer = completion.choices[0].message.content
            return answer

        for i in range(50):  # Retry up to 50 times in case of network failure
            try:
                answer = send_request(messages)
                break
            except Exception as e:
                print("Exception:", e)
                time.sleep(5)
        else:
            raise Exception("Failed to get response from the model.")

        return answer # str like "Choice: [2]"

class AgentRandom(AgentBase):
    def __init__(self, log_file=None) -> None:
        super().__init__("random", log_file)

    def generate(self):
        # Randomly choose an action from the options
        action_number = random.randint(1, 6)
        return f"Choice: [{action_number}]"