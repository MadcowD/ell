==============
Multimodality 
==============

ell supports multimodal inputs and outputs, allowing you to work with text, images, audio, and more.

.. code-block:: python

   from PIL import Image

   @ell.simple(model="gpt-4-vision")
   def describe_image(image: Image.Image):
       return [
           ell.system("Describe the contents of the image."),
           ell.user([ell.ContentBlock(text="What's in this image?"), ell.ContentBlock(image=image)])
       ]