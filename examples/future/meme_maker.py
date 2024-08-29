from PIL import Image
import numpy as np
import cv2
import os

import ell
ell.config.verbose = True

# Load the cat meme image using PIL
cat_meme_pil = Image.open(os.path.join(os.path.dirname(__file__), "catmeme.jpg"))

@ell.simple(model="gpt-4o", temperature=0.5)
def make_a_joke_about_the_image(image: Image.Image) -> str:
    return [
        ell.system("You are a comedian. Make a joke about the image."),
        ell.user(image)
    ]


if __name__ == "__main__":
    ell.set_store('sqlite_example', autocommit=True)
    joke = make_a_joke_about_the_image(cat_meme_pil)
    print(joke)