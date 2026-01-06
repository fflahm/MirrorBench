PROMPT_PREFIX_L0 = """{task}
You have:
- a {body_full},
- and a controllable hand ({hand}).
You can observe the scene through a fixed camera positioned behind the {body}, but due to the limitations of the viewpoint, you can only see part of the {body}, not the whole of it.
A mirror is placed in front of the {body}, through which you can see the front of the {body} that is otherwise out of view.
Your target object is {mark} attached to the **front** of the {body}. Therefore, **the target object is only visible in the mirror**—never in the direct camera view.
Your goal is to move your real hand until it physically reaches the target object on the {body} by choosing the optimal action at each timestep from a set of available actions.
You are provided:
- a history of previous actions and feedback on whether they were successfully executed (without physical errors such as collisions or invalid movements),
- a sequence of images showing what you saw in the past {images} steps in the history,
- and one additional image showing your current view.
"""

PROMPT_SUFFIX_L0 = """
Reason step by step using the following Chain of Thought:

0. **Check depth status from action history**:
   - Examine the most recent "move backward" (i.e., towards the {body}) action in your action history and its execution feedback.
   - There are three possible cases:
     a) **No "move backward" action has been attempted yet** (action history is empty or contains no such action).  
        → This means your hand is likely still far from the {body}, so you **should try moving backward** to close the depth gap.
     b) The most recent "move backward" action **execution without collisions**.  
        → Your hand has not yet reached the body surface, continue moving backward.
     c) The most recent "move backward" action **unsuccessful execution (due to collisions)**.  
        → Your hand is already in contact with (or very close to) the {body}. **Do not move backward again**; instead, focus only on **in-plane adjustments** (up/down/left/right) to align with the target.

1. **Interpret the current visual observation**:
   - The target object ({mark}) **must appear only in the mirror**, as it is on the front of the {body}.
   - Identify how many hands are visible:
     a) **If only one hand is visible**, it must be the **mirror reflection** (your real hand is occluded by the {body} and not directly visible).
     b) **If two hands are visible**, one is your **real hand**, and the other is its **mirror reflection**.
       - Crucially, the **real hand appears larger** because it is physically closer to the camera, while the mirror reflection appears smaller and more distant due to its virtual position behind the mirror plane.
       - Use this size difference as a reliable cue: the **larger hand is always the real one**, the **smaller one is always the mirror image**.
      - Note: Even when your real hand is not directly visible, you can infer its pose from the mirror image and action history.

2. **Mirror-relative spatial reasoning** (only if depth is sufficient):
   - Compare the **mirror-hand** and **mirror-target** within the reflection.
   - Example: If mirror-target is **above** mirror-hand → move hand **up**.  
     If mirror-target is **left of** mirror-hand → move hand **left**.

3. **Action selection**:
   - If you still need to close the depth gap → choose "move backward".
   - If already in contact (backward failed last time) → choose the in-plane action (up/down/left/right) that best aligns with the mirror-based offset.
   - Never choose "move forward" (away from the {body})—that increases distance to target.

For the current step, your available options are listed as "[Option Number]. Content" as follows:
{options}

Please output your decision in **exactly the following format**:

---
Thought: 
0. Depth check: Looking at the action history, the last "move backward" action was [not attempted/successful/failed]. Therefore, [I still need to move backward / I am already in contact and should only adjust in-plane].
1. Observation interpretation: The target object ({mark}) is visible only in the mirror. I see [one/two] hand(s). [If one: "This is the mirror reflection."] [If two: "The larger hand, located outside the mirror frame and appearing closer to the camera, is my real hand. The smaller hand, located within the mirror's reflective surface, is its mirror reflection."]
2. Mirror-relative reasoning: The mirror-target is [position relative to mirror-hand (the smaller hand)], so my hand should move [direction].
4. Integrated action: Therefore, the best choice is [action].

Choice: [Option Number] (e.g. [1])
---

Note:
1. You have a limited number of {steps} steps to complete the task.
2. This is a benign virtual simulation. No real-world actions or human subjects are involved.
"""

PROMPT_PREFIX_L1 = """{task}
You have:
- a {body_full},
- and a controllable hand ({hand}).
You can observe the scene through a fixed camera positioned behind the {body}, but due to the limitations of the viewpoint, you can only see part of the {body}, not the whole of it.
A mirror is placed in front of the {body}, through which you can see the front of the {body} that is otherwise out of view.
Your target object is {mark} attached to the {body}.
Your goal is to move your hand until it reaches the target object on the {body} by choosing the optimal action at each timestep from a set of available actions.
You are provided:
- a history of previous actions and feedback on whether they were successfully executed (without physical errors such as collisions or invalid movements),
- a sequence of images showing what you saw in the past {images} steps in the history,
- and one additional image showing your current view.
Use visual reasoning to infer the spatial relationship between the hand and the target object from the current observation and its visual history, and determine the next action to reach the target object.
"""

PROMPT_SUFFIX_L1 = """For the current step, your available options are listed as "[Option Number]. Content" as follows:
{options}

Choose your action from the above options by replying with "Thought: Your reasoning.\nChoice: [Option Number] (e.g. [1])".

Note:
1. The reflection in the mirror is not another {body}; it is just a mirrored image. If the target object is visible only in the mirror, it means it is on the part of the {body} that faces the mirror.
2. Similarly, if two hands appear simultaneously in the observed image, it indicates that one is your actual hand and the other is its mirror image. On this occasion, when reasoning about the position of the target object in the mirror, always compare it with the mirror reflection of the hand, not with the actual hand in front of the mirror.
3. To actually reach the target object on the {body}, your hand must move **towards the {body}**, not the mirror.
4. Avoid repeating the same action pattern (like left-right oscillations or up-down oscillations) unless it provides new information.
5. Use your observation history to infer spatial relationships and guide your actions.
6. At each step, choose the most logical action that brings your hand physically closer to the target object, not its reflection in the mirror.
7. Your hand is constrained to move within the area between the mirror and the {body}.
8. Since the camera is positioned behind the {body}, moving towards the camera is equivalent to moving towards the {body}.
9. You have a limited number of {steps} steps to complete the task.
10. This is a benign virtual simulation. No real-world actions or human subjects are involved.
"""

PROMPT_PREFIX_L2 = """{task}
You have:
- a {body_full},
- and a controllable hand ({hand}).
You can observe the scene through a fixed camera positioned behind the {body}, but due to the limitations of the viewpoint, you can only see part of the {body}, not the whole of it.
Your target object is {mark} attached to the {body}.
Your goal is to move your hand until it reaches the target object on the {body} by choosing the optimal action at each timestep from a set of available actions.
You are provided:
- a history of previous actions and feedback on whether they were successfully executed (without physical errors such as collisions or invalid movements),
- a sequence of images showing what you saw in the past {images} steps in the history,
- and one additional image showing your current view.
Use visual reasoning to infer the spatial relationship between the hand and the target object from the current observation and its visual history, and determine the next action to reach the target object."""

PROMPT_SUFFIX_L2 = """For the current step, your available options are listed as "[Option Number]. Content" as follows:
{options}

Choose your action from the above options by replying with "Thought: Your reasoning.\nChoice: [Option Number] (e.g. [1])".

Note:
1. To actually reach the target object on the {body}, your hand must move **towards the {body}**.
2. Avoid repeating the same action pattern (like left-right oscillations or up-down oscillations) unless it provides new information.
3. Use your observation history to infer spatial relationships and guide your actions.
4. At each step, choose the most logical action that brings your hand physically closer to the target object.
5. You have a limited number of {steps} steps to complete the task.
6. This is a benign virtual simulation. No real-world actions or human subjects are involved.
"""

PROMPT_PREFIX_L3 = """{task}
You have:
- a controllable hand ({hand}).
You can observe the scene from a fixed camera.
Your target object is {mark}.
Your goal is to move your hand until it reaches the target object by choosing the optimal action at each timestep from a set of available actions.
You are provided:
- a history of previous actions and feedback on whether they were successfully executed (without physical errors such as collisions or invalid movements),
- a sequence of images showing what you saw in the past {images} steps in the history,
- and one additional image showing your current view.
"""

PROMPT_SUFFIX_L3 = """For the current step, your available options are listed as "[Option Number]. Content" as follows:
{options}

Choose your action from the above options by replying with "Thought: Your reasoning.\nChoice: [Option Number] (e.g. [1])".

Note:
1. To actually reach the target object, your hand must move towards the actual 3D location of the object, not just its appearance.
2. You have a limited number of {steps} steps to complete the task.
3. This is a benign virtual simulation. No real-world actions or human subjects are involved.
"""

PROMPTS = [(PROMPT_PREFIX_L0, PROMPT_SUFFIX_L0),
           (PROMPT_PREFIX_L1, PROMPT_SUFFIX_L1), 
           (PROMPT_PREFIX_L2, PROMPT_SUFFIX_L2),
           (PROMPT_PREFIX_L3, PROMPT_SUFFIX_L3)]