from PIL import Image
import numpy as np
import cv2
import os

import ell
from ell.util.plot_ascii import plot_ascii


# Load the cat meme image using PIL
cat_meme_pil = Image.open(os.path.join(os.path.dirname(__file__), "catmeme.jpg"))

@ell.simple(model="gpt-4o", temperature=0.5)
def make_a_joke_about_the_image(image: Image.Image):
    return [
        ell.system("You are a meme maker. You are given an image and you must make a joke about it."),
        ell.user(image)
    ]


if __name__ == "__main__":
    ell.init(store='./logdir', autocommit=True, verbose=True)
    joke = make_a_joke_about_the_image(cat_meme_pil)
    print(joke)