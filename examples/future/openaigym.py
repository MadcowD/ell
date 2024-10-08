
ACTIONS = """
Action Space
There are four discrete actions available:

0: do nothing

1: fire left orientation engine

2: fire main engine

3: fire right orientation engine"""

from typing import List

from pydantic import BaseModel, Field
import ell2a

import numpy as np

class Action(BaseModel):
    reasoning: str = Field(description="The reasoning for the action to take")
    action: int = Field(description="The action to take, must be 0 ( go down ), 1, 2 (left) (go up), or 3 (right)")

x = Action(reasoning="", action=0)
@ell2a.complex(model="gpt-4o-2024-08-06", temperature=0.1, response_format=Action)
def control_game(prev_renders: List[np.ndarray], current_state : str):
    return [
        ell2a.system("""You are an lunar landar. Youur goal is to land on the moon by getting y to 0.. RULES:
                   
Your goal is to go downwards.
If you can't see your lunar landar, go down.
Never let your y height exceed 1. Go Output action 0 if y > 1.
To go down output the action 0.
If youu go down to fast you will crash.
Keep your angle as close to 0 as possible by using the left and right orientation engines.
                   
You will be given the following actions:
{actions}
Only return the action, do not include any other text.
        """.format(actions=ACTIONS)),
        ell2a.user([
            f"Current state vector (8-dimensional):",
            f"1. x coordinate: {current_state[0]}",
            f"2. y coordinate: {current_state[1]}",
            f"3. x velocity: {current_state[2]}",
            f"4. y velocity: {current_state[3]}",
            f"5. angle: {current_state[4]}",
            f"6. angular velocity: {current_state[5]}",
            f"7. left leg contact: {current_state[6]}",
            f"8. right leg contact: {current_state[7]}",
            f"Previous 3 renders (15 frames apart):",
            *prev_renders
        ])
    ]    

ell2a.init(verbose=True, store='./logdir')
import gymnasium as gym
env = gym.make("LunarLander-v2", render_mode="rgb_array")
observation, info = env.reset(seed=42)
import cv2
import numpy as np
import time

FRAME_RATE = 30
SKIP_DURATION = 1
FRAMES_TO_SKIP = 10
import PIL 
from PIL import Image

def render_and_display(env, rgb):
    # Resize the RGB image to a smaller version with height 160
    # Convert RGB array to BGR for OpenCV
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    # Resize the image to make it larger (optional)
    bgr_resized = cv2.resize(bgr, (800, 600), interpolation=cv2.INTER_AREA)

    # Display the image
    cv2.imshow('LunarLander', bgr_resized)
    cv2.waitKey(1)


observation, info = env.reset()
prev_action = 0
prev_render_buffer = []


for _ in range(1000):
    frame_count = 0
    start_time = time.time()

    render = env.render()
    small_rgb = cv2.resize(render, (160, 160), interpolation=cv2.INTER_AREA)
    # image = Image.fromarray(render)
    prev_render_buffer.append(small_rgb)
    if len(prev_render_buffer) > 3:
        prev_render_buffer.pop(0)
    render_and_display(env, render)



    action = (control_game(prev_renders=prev_render_buffer, current_state=observation)).parsed.action


    observation, reward, terminated, truncated, info = env.step(action)
    prev_action = action

    # skip frames
    for _ in range(FRAMES_TO_SKIP):
        observation, reward, terminated, truncated, info = env.step(prev_action)

        render = env.render()
        render_and_display(env, render)


    if terminated or truncated:
        break


env.close()