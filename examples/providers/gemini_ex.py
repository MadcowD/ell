""" 
Google Gemini example: pip install ell-ai[google]
"""
import ell
from google import genai

ell.init(verbose=True)

# custom client
client = genai.Client()

from PIL import Image, ImageDraw

# Create a new image with white background
img = Image.new('RGB', (512, 512), 'white')

# Create a draw object
draw = ImageDraw.Draw(img)

# Draw a red dot in the middle (using a small filled circle)
center = (256, 256)  # Middle of 512x512
radius = 5  # Size of the dot
draw.ellipse([center[0]-radius, center[1]-radius, 
              center[0]+radius, center[1]+radius], 
              fill='red')


@ell.simple(model='gemini-2.0-flash', client=client, max_tokens=10000)
def chat(prompt: str):
    return [ell.user([prompt + " what is in this image", img])]

print(chat("Write me a really long story about"))