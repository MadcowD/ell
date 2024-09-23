==============
Multimodality
==============

As the capabilities of language models continue to expand, so too does the need for frameworks that can seamlessly handle multiple modalities of input and output. ell rises to this challenge by providing robust support for multimodal interactions, allowing developers to work with text, images, audio, and more within a unified framework.

The Evolution of Multimodal Interactions
----------------------------------------

Traditionally, working with language models has been primarily text-based. However, the landscape is rapidly changing. Models like GPT-4 with vision capabilities, or DALL-E for image generation, have opened up new possibilities for multimodal applications. This shift presents both opportunities and challenges for developers.

Consider the complexity of constructing a prompt that includes both text and an image using a traditional API:

.. code-block:: python

    result = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
                ]
            }
        ]
    )

This approach, while functional, is verbose and can become unwieldy as the complexity of inputs increases. It doesn't align well with the natural flow of programming and can make code less readable and more error-prone.

ell's Approach to Multimodality
-------------------------------

ell addresses these challenges by treating multimodal inputs and outputs as first-class citizens within its framework. Let's explore how ell simplifies working with multiple modalities:

1. Simplified Input Construction

ell's Message and ContentBlock objects, which we explored in the Message API chapter, shine when it comes to multimodal inputs. They allow for intuitive construction of complex prompts:

.. code-block:: python

    from PIL import Image
    import ell

    @ell.simple(model="gpt-4-vision-preview")
    def describe_image(image: Image.Image):
        return [
            ell.system("You are a helpful assistant that describes images."),
            ell.user(["What's in this image?", image])
        ]

    result = describe_image(some_pil_image) # 'There's a cat in the image'

Notice how ell automatically handles the conversion of the PIL Image object into the appropriate format for the language model. This abstraction allows developers to focus on their application logic rather than the intricacies of API payloads.

ell also supports working with image URLs, making it easy to reference images hosted online:

.. code-block:: python

    from ell.types.message import ImageContent

    @ell.simple(model="gpt-4o-2024-08-06")
    def describe_image_from_url(image_url: str):
        return [
            ell.system("You are a helpful assistant that describes images."),
            ell.user(["What's in this image?", ImageContent(url=image_url, detail="low")])
        ]

    result = describe_image_from_url("https://example.com/cat.jpg")

This flexibility allows developers to work with both local images and remote image URLs seamlessly within the ell framework.

2. Flexible Output Handling

Just as ell simplifies input construction, it also provides flexible ways to handle multimodal outputs. The Message object returned by ``@ell.complex`` decorators offers convenient properties for accessing different types of content:

.. code-block:: python

    @ell.complex(model="gpt-5-omni")
    def generate_audiovisual_novel(topic : str):
        return [
            ell.system("You are a helpful assistant that can generate audiovisual novels. Output images, text, and audio simultaneously."),
            ell.user("Generate a novel on the topic of {topic}")
        ]

.. code-block:: python

    >>> result = generate_audiovisual_novel("A pirate adventure")
    Message(role="assistant", content=[
        ContentBlock(type="text", text="Chapter 1: The Treasure Map"),
        ContentBlock(type="image", image=PIL.Image.Image(...)),
        ContentBlock(type="text", text="The crew of the ship set sail on a quest to find the lost treasure of the pirate king. They must navigate treacherous waters, avoid the wrath of the sea monsters, and outsmart the other pirates who are also searching for the treasure."),
        ContentBlock(type="audio", audio=np.array([...])),
    ])

.. code-block:: python

    if result.images:
        for img in result.images:
            display(img)
    
    if result.text:
        print(result.text)

    if result.audios:
        for audio in result.audios:
            play(audio)

This approach allows for intuitive interaction with complex, multimodal outputs without the need for extensive parsing or type checking.

3. Seamless Integration with Python Ecosystem

ell's design philosophy extends to its integration with popular Python libraries for handling different media types. For instance, it works seamlessly with PIL for images, making it easy to preprocess or postprocess visual data:

.. code-block:: python

    from PIL import Image, ImageEnhance

    def enhance_image(image: Image.Image) -> Image.Image:
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(1.5)

    @ell.complex(model="gpt-4-vision-preview")
    def analyze_enhanced_image(image: Image.Image):
        enhanced = enhance_image(image)
        return [
            ell.system("Analyze the enhanced image and describe any notable features."),
            ell.user(enhanced)
        ]

This example demonstrates how ell allows for the seamless integration of image processing techniques within the language model workflow.

The Power of Multimodal Composition
-----------------------------------

One of the most powerful aspects of ell's multimodal support is the ability to compose complex workflows that involve multiple modalities. Let's consider a more advanced example:

.. code-block:: python

    @ell.simple(model="gpt-4o")
    def generate_image_caption(image: Image.Image):
        return [
            ell.system("Generate a concise, engaging caption for the image."),
            ell.user(image)
        ]

    @ell.complex(model="gpt-4-audio")
    def text_to_speech(text: str):
        return [
            ell.system("Convert the following text to speech."),
            ell.user(text)
        ]

    @ell.complex(model="gpt-4")
    def create_social_media_post(image: Image.Image):
        caption = generate_image_caption(image)
        audio = text_to_speech(caption)
        
        return [
            ell.system("Create a social media post using the provided image, caption, and audio."),
            ell.user([
                "Image:", image,
                "Caption:", caption,
                "Audio:", audio.audios[0]
            ])
        ]

    post = create_social_media_post(some_image)

In this example, we've created a workflow that takes an image, generates a caption for it, converts that caption to speech, and then combines all these elements into a social media post. ell's multimodal support makes this complex interaction feel natural and intuitive.

Multimodality in ell isn't just a feature; it's a fundamental design principle that reflects the evolving landscape of AI and machine learning. By providing a unified, intuitive interface for working with various types of data, ell empowers developers to create sophisticated, multimodal applications with ease.
