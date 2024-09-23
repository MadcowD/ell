import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import logging
import os

# Load pre-rendered character bitmaps
try:
    package_dir = os.path.dirname(__file__)
    bitmaps_path = os.path.join(package_dir, 'char_bitmaps.npy')
    data = np.load(bitmaps_path, allow_pickle=True).item()
    char_bitmaps = data['char_bitmaps']
    max_char_width = data['max_char_width']
    max_char_height = data['max_char_height']


    ASCII_CHARS = " .:-=+*#%@"
    def plot_ascii(
        image: Image.Image,
        width: int = 100,
        color: bool = True,
    ):
        """
        Convert a PIL Image to ASCII art using pre-rendered character bitmaps and print it to the console with optional coloring.
        """
        num_chars = len(ASCII_CHARS)


        # Adjust the scaling factor to compensate for character aspect ratio
        scale = 0.5  # You can tweak this value based on your terminal's character dimensions
        aspect_ratio = image.height / image.width
        new_width = width
        new_height = int(aspect_ratio * new_width * (max_char_height / max_char_width) * scale)
        image = image.resize((new_width * max_char_width, new_height * max_char_height)).convert('RGB')

        # Convert image to NumPy array
        img_array = np.array(image)

        # Compute brightness using luminance formula
        luminance = 0.2126 * img_array[:, :, 0] + 0.7152 * img_array[:, :, 1] + 0.0722 * img_array[:, :, 2]

        # Normalize brightness to range 0-1
        brightness_normalized = luminance / 255

        if color:
            # Get RGB values for coloring
            r = img_array[:, :, 0]
            g = img_array[:, :, 1]
            b = img_array[:, :, 2]

        # Compute the number of blocks
        y_blocks = new_height
        x_blocks = new_width

        # Reshape brightness_normalized to (y_blocks, max_char_height, x_blocks, max_char_width)
        brightness_blocks = brightness_normalized.reshape(y_blocks, max_char_height, x_blocks, max_char_width)
        brightness_blocks = brightness_blocks.mean(axis=(1, 3))  # Average over each block

        # Normalize again if necessary
        brightness_blocks = brightness_blocks / brightness_blocks.max()

        # Vectorize the selection of ASCII characters
        indices = np.digitize(brightness_blocks, np.linspace(0, 1, num_chars)) - 1
        indices = np.clip(indices, 0, num_chars - 1)
        ascii_chars = np.array(list(ASCII_CHARS))[indices]

        if color:
            # Compute average color for each block
            r_blocks = r.reshape(y_blocks, max_char_height, x_blocks, max_char_width).mean(axis=(1, 3)).astype(int)
            g_blocks = g.reshape(y_blocks, max_char_height, x_blocks, max_char_width).mean(axis=(1, 3)).astype(int)
            b_blocks = b.reshape(y_blocks, max_char_height, x_blocks, max_char_width).mean(axis=(1, 3)).astype(int)

            # Convert RGB to 8-bit color code
            color_codes = 16 + (36 * (r_blocks // 51)) + (6 * (g_blocks // 51)) + (b_blocks // 51)
            color_codes = color_codes.astype(str)

            # Create colored ASCII characters
            colored_ascii = np.char.add(np.char.add("\033[38;5;", color_codes), "m")
            colored_ascii = np.char.add(colored_ascii, np.char.add(ascii_chars, "\033[0m"))

            # Join characters into lines
            ascii_image = ["".join(row) for row in colored_ascii]
        else:
            ascii_image = ["".join(row) for row in ascii_chars]

        # Print the ASCII image
        return ascii_image
except FileNotFoundError:
    def plot_ascii(
        image: Image.Image,
        width: int = 100,
        color: bool = True,
    ):
        return "<image>"

# For packaging .
def render_and_save_char_bitmaps(
    font_path: str = "Courier New.ttf",
    font_size: int = 10,
    output_path: str = "char_bitmaps.npy"
) -> None:
    num_chars = len(ASCII_CHARS)
    char_bitmaps = {}
    max_char_width, max_char_height = 0, 0

    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        logging.error(f"Font file '{font_path}' not found. Please provide a valid path.")
        sys.exit(1)

    for char in ASCII_CHARS:
        char_image = Image.new('L', (font_size, font_size), color=255)
        draw = ImageDraw.Draw(char_image)
        bbox = font.getbbox(char)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text(((font_size - w) / 2, (font_size - h) / 2), char, fill=0, font=font)
        bitmap = np.array(char_image) / 255  # Normalize to 0-1
        char_bitmaps[char] = bitmap
        max_char_width = max(max_char_width, bitmap.shape[1])
        max_char_height = max(max_char_height, bitmap.shape[0])

    # Save the character bitmaps and max dimensions
    data = {
        'char_bitmaps': char_bitmaps,
        'max_char_width': max_char_width,
        'max_char_height': max_char_height
    }
    np.save(output_path, data)
    logging.info(f"Character bitmaps saved to '{output_path}'.")

