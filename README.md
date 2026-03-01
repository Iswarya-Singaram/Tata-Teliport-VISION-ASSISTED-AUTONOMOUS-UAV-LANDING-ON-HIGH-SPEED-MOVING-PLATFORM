# Tata-Teliport-VISION-ASSISTED-AUTONOMOUS-UAV-LANDING-ON-HIGH-SPEED-MOVING-PLATFORM

 CAD Design File link : https://drive.google.com/file/d/1Pvf7DOd3Uwe8qZvV4OjSlF0PgbxM-7SX/view?usp=sharing

An integrated hardware and software stack for precision drone recovery on moving platforms (trains/trucks) using **Sensor Fusion**, **LoRa Telemetry**, and **Computer Vision**.

---

## 📌 Project Overview
Landing a drone on a moving vehicle is a complex "Relative Navigation" problem. This project solves it by fusing long-range predictive tracking (via LoRa) with short-range visual servoing (via ArUco markers).

### Key Features
* **Dual-Layer Synchronization:** Uses LoRa to match the vehicle's velocity vector before visual acquisition.
* **Precision Computer Vision:** Raspberry Pi-based ArUco detection for centimeter-level landing accuracy.
* **Crosswind Compensation:** Fuses Pitot tube airspeed with GPS groundspeed to adjust tilt and thrust dynamically.
* **Fail-Safe Redundancy:** Automatic transition to Optical Flow and IMU dead-reckoning if GPS or Comms are lost.

---

## 🛠 Tech Stack
| Component | Technology |
| :--- | :--- |
| **Flight Controller** | Pixhawk (ArduPilot/PX4) |
| **Companion Computer** | Raspberry Pi 4/5 |
| **Vision Processing** | OpenCV + Python |
| **Communication** | ESP32 + LoRa (868/915 MHz) |
| **Positioning** | RTK GPS + Laser Rangefinder |
| **Telemetry** | MAVLink Protocol |

---

## 🛰 System Architecture

### 1. The "Handshake" (Long Range)
The vehicle broadcasts its GPS coordinates and velocity vector via an **ESP32 + LoRa** transmitter. The drone's Raspberry Pi calculates an intercept trajectory and commands the Pixhawk to match the vehicle's speed.

### 2. Terminal Approach (Short Range)
Once the drone is within 15 meters, the onboard camera identifies the **ArUco Marker**. The system switches from Global GPS coordinates to **Relative Vision Coordinates** ($X, Y, Z$ offsets).

### 3. Final Recovery
The drone utilizes a **Kalman Filter** to fuse:
* **Optical Flow:** For horizontal deck stability.
* **Lidar/Rangefinder:** For precise altitude above the roof.
* **IMU:** To compensate for vehicle vibration.

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/drone-moving-landing.git](https://github.com/yourusername/drone-moving-landing.git)
   cd drone-moving-landing
