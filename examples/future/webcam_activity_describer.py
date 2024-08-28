import cv2
import time
from PIL import Image
import numpy as np
import ell
import pygame

ell.config.verbose = True

# Initialize pygame mixer
pygame.mixer.init()

# Create a simple beep sound (stereo)
pygame.sndarray.use_arraytype('numpy')
sample_rate = 44100
duration = 0.2  # 0.2 seconds
t = np.linspace(0, duration, int(sample_rate * duration), False)
beep = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
beep = (beep * 32767).astype(np.int16)
stereo_beep = np.column_stack((beep, beep))  # Create stereo sound
beep_sound = pygame.sndarray.make_sound(stereo_beep)

@ell.simple(model="gpt-4o-mini", temperature=0.1)
def describe_activity(image: Image.Image) -> str:
    return [
        ell.system("You are an observant assistant. Respond with TRUE if the person in the image is touching their nose."),
        ell.user(image)
    ]

def capture_webcam_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        # Resize the image to a smaller 16:9 size, e.g., 160x90
        return image.resize((160, 90), Image.LANCZOS)
    return None

def parse_and_beep(description):
    if "TRUE" in description.upper():
        print("\n" + "*" * 20)
        print("* NOSE TOUCH DETECTED *")
        print("*" * 20 + "\n")
        # Play the beep sound
        beep_sound.play()
    return description

if __name__ == "__main__":
    ell.set_store('sqlite_example', autocommit=True)
    
    print("Press Ctrl+C to stop the program.")
    try:
        while True:
            image = capture_webcam_image()
            if image:
                description = describe_activity(image)
                parsed_description = parse_and_beep(description)
                print(f"Activity: {parsed_description}")
            else:
                print("Failed to capture image from webcam.")
            # time.sleep(1)
    except KeyboardInterrupt:
        print("Program stopped by user.")
    finally:
        pygame.mixer.quit()