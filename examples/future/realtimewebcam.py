import cv2
import time
from PIL import Image
import os
from ell.util.plot_ascii import plot_ascii


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print("Press Ctrl+C to stop the program.")
    cap = cv2.VideoCapture(1)  # Change to 0 for default camera
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture image from webcam.")
                continue

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = Image.fromarray(frame)
            
            # Resize the frame
            # frame = frame.resize((40*4, 30*4), Image.LANCZOS)

            ascii_image = plot_ascii(frame, width=120, color=True)
            clear_console()
            print("\n".join(ascii_image))
            
            # Add a small delay to control frame rate
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Program stopped by user.")
    finally:
        cap.release()

if __name__ == "__main__":
    main()
