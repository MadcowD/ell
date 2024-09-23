from typing import List
import cv2
import time
from PIL import Image
import ell
from ell.types.message import ImageContent
from ell.util.plot_ascii import plot_ascii

ell.init(verbose=True, store='./logdir', autocommit=True)

@ell.simple(model="gpt-4o", temperature=0.1)
def describe_activity(image: Image.Image):
    return [
        ell.system("You are VisionGPT. Answer <5 words all lower case."),
        ell.user(["Describe what the person in the image is doing:", ImageContent(image=image, detail="low")])
    ]


def capture_webcam_image():
    cap = cv2.VideoCapture(0)
    for _ in range(10):
        ret, frame = cap.read()
    ret, frame = cap.read()
    
    cap.release()
    if ret:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        # Resize the image to a smaller 16:9 size, e.g., 160x90
        return image.resize((160, 90), Image.LANCZOS)
    return None

if __name__ == "__main__":

    print("Press Ctrl+C to stop the program.")
    try:
        while True:
            image = capture_webcam_image()
            if image:
                description = describe_activity(image)
                print(f"Activity: {description}")
            else:
                print("Failed to capture image from webcam.")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program stopped by user.")

