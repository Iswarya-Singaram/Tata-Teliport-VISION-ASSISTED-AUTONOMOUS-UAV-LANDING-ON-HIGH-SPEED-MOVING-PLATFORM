import cv2
import cv2.aruco as aruco
import numpy as np
from pymavlink import mavutil
import serial
import time
import threading

# --- CONFIGURATION ---
MARKER_SIZE = 0.20  # 20cm
# REPLACE THESE with your actual calibration results!
CAMERA_MATRIX = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=float)
DIST_COEFFS = np.zeros((5, 1))

# --- CONNECTIONS ---
# Pixhawk Connection
pixhawk = mavutil.mavlink_connection('/dev/ttyAMA0', baud=921600)
# LoRa Connection (ESP32 via USB or Serial)
lora_serial = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

# Global variables for LoRa telemetry
train_lat, train_lon, train_vel_x, train_vel_y = 0, 0, 0, 0

def lora_listener():
    """Background thread to update train position from ESP32."""
    global train_lat, train_lon, train_vel_x, train_vel_y
    while True:
        if lora_serial.in_waiting > 0:
            line = lora_serial.readline().decode('utf-8').strip()
            # Expecting CSV: "lat,lon,vx,vy"
            try:
                data = line.split(',')
                train_lat, train_lon = float(data[0]), float(data[1])
                train_vel_x, train_vel_y = float(data[2]), float(data[3])
            except:
                pass

# Start LoRa thread
threading.Thread(target=lora_listener, daemon=True).start()

def send_velocity_matching(vx, vy):
    """Tell Pixhawk to match the train's speed (m/s) in Guided Mode."""
    pixhawk.mav.set_position_target_local_ned_send(
        0, pixhawk.target_system, pixhawk.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b0000111111000111, # Use only Velocity bits
        0, 0, 0,            # Positions (not used)
        vx, vy, 0,          # Velocities (m/s)
        0, 0, 0,            # Acceleration (not used)
        0, 0                # Yaw
    )

def send_landing_target(x, y, z):
    """Precision landing offsets via ArUco."""
    pixhawk.mav.landing_target_send(
        int(time.time() * 1e6), 0,
        mavutil.mavlink.MAV_FRAME_BODY_NED,
        float(x), float(y), float(z), 0, 0
    )

# --- MAIN LOOP ---
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()
cap = cv2.VideoCapture(0)

print("System Active. Waiting for Target...")

try:
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # 1. MATCH SPEED (LoRa)
        # Even if we don't see the marker, match the train's velocity
        send_velocity_matching(train_vel_x, train_vel_y)

        # 2. FIND MARKER (Vision)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        if ids is not None:
            rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(corners, MARKER_SIZE, CAMERA_MATRIX, DIST_COEFFS)
            
            # Map OpenCV to Drone NED (North-East-Down relative to drone body)
            target_fwd = tvecs[0][0][2] 
            target_right = tvecs[0][0][0]
            target_down = tvecs[0][0][1]

            # 3. OVERRIDE WITH PRECISION (Vision)
            send_landing_target(target_fwd, target_right, target_down)
            
            cv2.putText(frame, "LOCKED", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "SEARCHING (using LoRa)", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow('Drone AI Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
