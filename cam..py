from picamera2 import Picamera2
import time
import random

def capture_images(n):
    """Captures n images in full resolution and saves them with random filenames."""
    picam2 = Picamera2()
    #config = picam2.create_still_configuration()
    #picam2.configure(config)

     #✅ Configure full-resolution image capture
    config = picam2.create_still_configuration(main={"size": (4056, 3040)})  # Full 12MP resolution
    picam2.configure(config)

     #✅ Adjust camera settings for sharp, bright images
    picam2.set_controls({
         "ExposureTime": 4000,  # Shorter exposure reduces blur
         "AnalogueGain": 2.0,   # Boosts brightness
         "FrameRate": 30,       # Higher FPS reduces rolling shutter
         "AeEnable": True,      # Auto Exposure for dynamic lighting
         "Sharpness": 2.0,      # Enhances QR edges
         "Contrast": 1.5        # Improves QR visibility
    })  

    picam2.start()

    for i in range(n):
        time.sleep(1)  # Allow camera to adjust
        filename = f"captured_image_{random.randint(1000, 9999)}.jpg"

        # ✅ Capture full-resolution image directly (no array conversion)
        picam2.capture_file(filename)
        print(f"✅ Image {i+1} saved as {filename}")

    picam2.stop()
    print("✅ Finished capturing images.")

if __name__ == "__main__":
    capture_images(3)
