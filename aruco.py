import cv2
import numpy as np
from picamera2 import Picamera2
import time
import random
import torch
import pyzbar.pyzbar as pyzbar
import base64

def scan_qr_code_from_bbox(cropped_qr, filename_prefix, index):
    """ Scans the QR code from the cropped bounding box """
    decoded_objects = pyzbar.decode(cropped_qr)
    
    # Generate random filename for cropped QR image
    cropped_filename = f"{filename_prefix}_qr_{random.randint(1000, 9999)}.png"
    cv2.imwrite(cropped_filename, cropped_qr)  # Save cropped QR image
    print(f"Cropped QR saved as {cropped_filename}")

    for obj in decoded_objects:
        qr_data = obj.data.decode('utf-8')  # Decode QR content
        print(f"QR Data: {qr_data}")

        # Check if it's a base64-encoded image
        try:
            if qr_data.startswith("data:image"):
                header, encoded = qr_data.split(",", 1)
                image_data = base64.b64decode(encoded)
                image_filename = f"{filename_prefix}_qr_{index}.png"
                with open(image_filename, "wb") as img_file:
                    img_file.write(image_data)
                print(f"QR Image saved as {image_filename}")
            else:
                text_filename = f"{filename_prefix}_qr_{index}.txt"
                with open(text_filename, "w") as text_file:
                    text_file.write(qr_data)
                print(f"QR Text saved as {text_filename}")
        except Exception as e:
            print(f"Error processing QR: {e}")

def expand_bbox(x_min, y_min, x_max, y_max, frame, margin=0.1):
    """ Expands the bounding box size to ensure full QR code capture. """
    
    # Compute the margin in pixels
    width = x_max - x_min
    height = y_max - y_min
    expand_x = int(width * margin)
    expand_y = int(height * margin)

    # Expand bounding box
    x_min = max(0, x_min - expand_x)
    y_min = max(0, y_min - expand_y)
    x_max = min(frame.shape[1], x_max + expand_x)
    y_max = min(frame.shape[0], y_max + expand_y)

    return x_min, y_min, x_max, y_max

def image_process_by_yolov5_draw(frame, altitude=10):
    # Load YOLOv5 model
    model = torch.hub.load('/home/teju/yolov5', 'custom', path='./Downloads/best.pt', source='local', force_reload=True)
    results = model(frame)

    # Get detection results
    detections = results.pandas().xyxy[0]
    
    move_x_meters = 0
    move_y_meters = 0
    move_z_meters = 0
    if detections.empty:
        return [0,0];
    qr_bboxes = []  # Store bounding boxes for QR scanning
    
    if not detections.empty:
        for index, row in detections.iterrows():
            x_min, y_min, x_max, y_max = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            
            # Expand bounding box
            x_min, y_min, x_max, y_max = expand_bbox(x_min, y_min, x_max, y_max, frame)

            # Immediately scan the QR code after storing the bounding box
            cropped_qr = frame[y_min:y_max, x_min:x_max]
            # scan_qr_code_from_bbox(cropped_qr, "processed_qr", index)

            # Draw bounding box
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

            # Compute center of bounding box (QR code)
            center_x = (x_min + x_max) // 2
            center_y = (y_min + y_max) // 2

            # Compute image center
            img_center_x = frame.shape[1] // 2
            img_center_y = frame.shape[0] // 2

            # Draw line from image center to QR center
            cv2.line(frame, (img_center_x, img_center_y), (center_x, center_y), (0, 0, 255), 2)

            # Calculate offset in pixels
            offset_x = center_x - img_center_x  # Left/Right movement
            offset_y = center_y - img_center_y  # Forward/Backward movement

            # Convert pixel offset to meters
            fov_width_meters = 15.5  # Based on 75° FOV at 10m altitude
            pixels_per_meter = frame.shape[1] / fov_width_meters

            move_x_meters = offset_x / pixels_per_meter  # Left-Right movement in meters
            move_y_meters = offset_y / pixels_per_meter  # Forward-Backward movement in meters

            # Adjust altitude based on QR size
            """qr_width_meters = 1  # QR code actual size (1m)
            qr_pixel_width = x_max - x_min
            ideal_qr_pixel_width = (qr_width_meters / fov_width_meters) * frame.shape[1]
            altitude_adjustment = (ideal_qr_pixel_width - qr_pixel_width) * (altitude / ideal_qr_pixel_width)

            move_z_meters = altitude_adjustment  # Positive: Ascend, Negative: Descend"""
            # Store bounding box for QR scanning
            qr_bboxes.append([move_x_meters,move_y_meters])
    
    min_point = min(qr_bboxes, key=lambda b: math.sqrt(b[0]**2 + b[1]**2))

    return min_point ,frame # Return the processed frame with drawn bounding boxes

def capture_images(n):
    picam2 = Picamera2()
    config = picam2.create_still_configuration()
    picam2.configure(config)
    picam2.start()

    for i in range(n):
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
       
        filename = f"captured_image_{random.randint(100, 999)}.jpg"
        
        min_point,frame = image_process_by_yolov5_draw(frame)  # Get drawn image with bounding boxes
        cv2.imwrite(filename, frame)
        print(f"Image {i+1} saved as {filename}")
        return min_point

        time.sleep(3)  # Optional: Add a delay between captures

    picam2.stop()
    print("Finished capturing images.")

if __name__ == "__main__":
    n = 1
    print(n)
    min_point = capture_images(n)
    output = {
      "min_point":min_point
    }
    print(json.dumps(output))
