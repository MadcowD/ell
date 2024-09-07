Multimodal Inputs in ell
========================

Introduction
------------

ell supports multimodal inputs, allowing Language Model Programs (LMPs) to work with various types of data beyond just text. This feature enables more complex and rich interactions with language models, particularly useful for tasks involving images, audio, or structured data.

Supported Input Types
---------------------

ell currently supports the following input types:

1. Text
2. Images
3. Structured Data (via Pydantic models)

Future versions may include support for additional modalities like audio or video.

Working with Multimodal Inputs
------------------------------

Text Inputs
^^^^^^^^^^^

Text inputs are the most basic form and are handled as strings:

.. code-block:: python

    @ell.simple(model="gpt-4")
    def text_lmp(text_input: str) -> str:
        return f"Analyze this text: {text_input}"

Image Inputs
^^^^^^^^^^^^

To work with images, use the ``PIL.Image.Image`` type:

.. code-block:: python

    from PIL import Image

    @ell.simple(model="gpt-4-vision-preview")
    def image_analysis_lmp(image: Image.Image) -> str:
        return [
            ell.system("Analyze the given image and describe its contents."),
            ell.user([
                ell.ContentBlock(text="What do you see in this image?"),
                ell.ContentBlock(image=image)
            ])
        ]

    # Usage
    image = Image.open("example.jpg")
    description = image_analysis_lmp(image)
    print(description)

Structured Data Inputs
^^^^^^^^^^^^^^^^^^^^^^

For structured data, use Pydantic models:

.. code-block:: python

    from pydantic import BaseModel

    class UserProfile(BaseModel):
        name: str
        age: int
        interests: List[str]

    @ell.simple(model="gpt-4")
    def profile_analysis_lmp(profile: UserProfile) -> str:
        return f"Analyze this user profile:\n{profile.model_dump_json()}"

    # Usage
    user = UserProfile(name="Alice", age=30, interests=["reading", "hiking"])
    analysis = profile_analysis_lmp(user)
    print(analysis)

Combining Multiple Input Types
------------------------------

You can combine different input types in a single LMP:

.. code-block:: python

    @ell.complex(model="gpt-4-vision-preview")
    def multi_input_lmp(text: str, image: Image.Image, profile: UserProfile) -> List[ell.Message]:
        return [
            ell.system("You are an AI assistant capable of analyzing text, images, and user profiles."),
            ell.user([
                ell.ContentBlock(text=f"Analyze this text: {text}"),
                ell.ContentBlock(image=image),
                ell.ContentBlock(text=f"Consider this user profile: {profile.model_dump_json()}")
            ])
        ]

    # Usage
    text_input = "This is a sample text."
    image_input = Image.open("example.jpg")
    profile_input = UserProfile(name="Bob", age=25, interests=["sports", "music"])

    response = multi_input_lmp(text_input, image_input, profile_input)
    print(response.text)

Best Practices for Multimodal Inputs
------------------------------------

1. **Type Annotations**: Always use proper type annotations for your inputs to ensure ell handles them correctly.
2. **Input Validation**: For structured data, leverage Pydantic's validation capabilities to ensure data integrity.
3. **Clear Instructions**: When combining multiple input types, provide clear instructions to the language model on how to process each input.
4. **Model Compatibility**: Ensure the chosen language model supports the input types you're using (e.g., using a vision-capable model for image inputs).
5. **Input Size**: Be mindful of input sizes, especially for images, as there may be limitations on the maximum size supported by the model.

Handling Large Inputs
---------------------

For large inputs, especially images, you may need to resize or compress them before passing to the LMP:

.. code-block:: python

    from PIL import Image

    def prepare_image(image_path: str, max_size: tuple = (1024, 1024)) -> Image.Image:
        with Image.open(image_path) as img:
            img.thumbnail(max_size)
            return img

    # Usage
    prepared_image = prepare_image("large_image.jpg")
    result = image_analysis_lmp(prepared_image)

Conclusion
----------

Multimodal inputs in ell greatly expand the capabilities of your Language Model Programs, allowing them to process and analyze various types of data. By effectively combining different input modalities, you can create more sophisticated and context-aware AI applications.