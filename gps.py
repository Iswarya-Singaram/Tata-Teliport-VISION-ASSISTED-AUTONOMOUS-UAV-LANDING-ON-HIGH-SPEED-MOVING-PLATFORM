from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
from geopy.distance import geodesic
import subprocess

# Connect to the Vehicle
print("Connecting to the vehicle...")
vehicle = connect('/dev/ttyAMA0', wait_ready=True,baud=921600)  # Change to your SITL connection string or real drone


def scanningTask():
    python_3_10 = "/usr/bin/python3.11"  
    script_source = "/home/teju/cam.py"  

    try:
        subprocess.run([python_3_10, script_source], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: The script failed with exit code {e.returncode}")
    except FileNotFoundError:
        print("Error: Python interpreter or script not found")
    except Exception as e:
        print(f"Unexpected error: {e}")
        
        
# Function to get the home location from GPS
def get_home_location():
    print("Fetching GPS location for home coordinates...")
    while not vehicle.gps_0.fix_type or vehicle.gps_0.fix_type < 2:  # Wait for a 2D or better GPS fix
        print("Waiting for GPS fix...")
        time.sleep(1)
    home_lat = vehicle.location.global_frame.lat
    home_lon = vehicle.location.global_frame.lon
    print(f"Home location set: Latitude={home_lat}, Longitude={home_lon}")
    return home_lat, home_lon

# Function to arm and take off
def arm_and_takeoff(target_altitude):
    print("Arming motors...")
    while not vehicle.is_armable:
        print("Waiting for vehicle to initialize...")
        time.sleep(1)

    vehicle.mode = VehicleMode("GUIDED") 
     # Set the mode to GUIDED
    while not vehicle.mode.name=="GUIDED":
        print("vhanging mode") 
        time.sleep(1)
    vehicle.armed = True  # Arm the vehicle

    while not vehicle.armed:
        print("Waiting for arming...")
        time.sleep(1)

    print(f"Taking off to {target_altitude} meters...")
    vehicle.simple_takeoff(target_altitude)  # Take off to target altitude

    # Wait until the vehicle reaches the target altitude
    while True:
        print(f"Altitude: {vehicle.location.global_relative_frame.alt}")
        if vehicle.location.global_relative_frame.alt >= target_altitude * 0.95:
            print("Target altitude reached!")
            break
        time.sleep(1)

# Function to fly to a destination
def fly_to_destination(latitude, longitude, altitude):
    print(f"Flying to destination: Latitude={latitude}, Longitude={longitude}, Altitude={altitude}")
    target_location = LocationGlobalRelative(latitude, longitude, altitude)
    vehicle.simple_goto(target_location)

    # Wait until close to the target location
    while True:
        current_location = vehicle.location.global_relative_frame
        distance = get_distance_meters(current_location, target_location)
        print(f"Distance to target: {distance:.2f} meters")
        if distance < 1:  # Stop when within 1 meter of the target
            print("Reached destination!")
            break
        time.sleep(1)
        
        
def fly_to_destination_Alt(latitude, longitude, altitude):
    print(f"Flying to destination: Latitude={latitude}, Longitude={longitude}, Altitude={altitude}")
    target_location = LocationGlobalRelative(latitude, longitude, altitude)
    vehicle.simple_goto(target_location)

    last_distance = float('inf')  # Start with a very large distance
    consecutive_increases = 0  # Count how many times the distance increases

    while True:
        print(vehicle.location.global_relative_frame.alt)
        current_location = vehicle.location.global_relative_frame
        distance = get_distance_meters(current_location, target_location)
        print(f"Distance to target: {distance:.2f} meters")

        if distance < 1:  # Stop when within 1 meter of the target
            print("Reached destination!")
            break
        
        # Check if the distance is increasing
        if distance > last_distance:
            consecutive_increases += 1
        else:
            consecutive_increases = 0  # Reset if distance decreases

        # If distance increases for 3 consecutive checks, assume overshoot
        if consecutive_increases >= 3:
            print("Overshoot detected! Stopping...")
            vehicle.mode=VehicleMode("RTL")
            break

        last_distance = distance
        time.sleep(1)

# Function to calculate distance between two locations
def get_distance_meters(location1, location2):
    from math import sqrt, pow
    dlat = location2.lat - location1.lat
    dlong = location2.lon - location1.lon
    return sqrt(pow(dlat * 1.113195e5, 2) + pow(dlong * 1.113195e5, 2))
    
def get_distance_meters_Alt(location1, location2):
    coord1 = (location1.lat, location1.lon)
    coord2 = (location2.lat, location2.lon)
    return geodesic(coord1, coord2).meters

# Function to land
def land():
    print("Landing...")
    vehicle.mode = VehicleMode("LAND")
    while vehicle.armed:
        print("Waiting for landing...")
        time.sleep(1)
    print("Landed successfully!")
    

def disarm_and_task_alt():
    minAlt = 5
    maxAlt =10

    while vehicle.location.global_relative_frame.alt > minAlt:
        if vehicle.location.global_relative_frame.alt <= maxAlt:
            print("Waiting for drone to stabilize...")
            start_time = time.time()
            end_time =0
            true=True
            while time.time() - start_time < 5:  # Timeout after 5 seconds
                velocity = vehicle.velocity  # [vx, vy, vz]
                print(f"Current Velocity: {velocity}")
                if abs(velocity[0]) < 0.1 and abs(velocity[1]) < 0.1 and abs(velocity[2]) < 0.1:
                    print("Drone stabilized, capturing image...")
                    end_time=time.time()
                    true=False
                    scanningTask()
                    break
                time.sleep(0.5)
            if end_time - start_time >= 5 and true:
                print("Timeout reached, capturing image anyway...")
                scanningTask()
            print(f"Image taken at Altitude: {vehicle.location.global_relative_frame.alt}")
            
        # Calculate new target altitude
        currAlt = vehicle.location.global_relative_frame.alt-1
        new_location = LocationGlobalRelative(
            vehicle.location.global_frame.lat,
            vehicle.location.global_frame.lon,
            currAlt
        )

        vehicle.simple_goto(new_location)  # Command vehicle to descend
        start_time = time.time()
        timeout = 30 
        # Wait until vehicle reaches the target altitude
        while vehicle.location.global_relative_frame.alt > currAlt + 0.1:  # Add buffer to avoid infinite 
            if time.time() - start_time > timeout:
                print("Timeout reached! Forcing RTL.")
                vehicle.mode=VehicleMode("RTL")
                return
            print(f"Descending... Current Altitude: {vehicle.location.global_relative_frame.alt:.2f}m")
            time.sleep(1)

    print(f"Final Altitude: {vehicle.location.global_relative_frame.alt:.2f}m")
    
    print("Changing to Landing mode...")
    vehicle.mode = VehicleMode("LAND")
    time.sleep(8)

    print("Changing to RTL mode...")
    vehicle.mode = VehicleMode("RTL")


def disarm_and_task():
    minAlt=3
    maxAlt=8

    
    while vehicle.location.global_frame.alt > minAlt:
        if(vehicle.location.global_frame.alt <= maxAlt):
            scanningTask()
        currAlt = vehicle.location.global_frame.alt - 1 
        new_location = LocationGlobalRelative(vehicle.location.global_frame.lat,
                                              vehicle.location.global_frame.lon,
                                              currAlt)
        vehicle.simple_goto(new_location)

        while vehicle.location.global_frame.alt > currAlt:
            print(f"Descending... Current Altitude: {vehicle.location.global_frame.alt}")
            time.sleep(1)
    
    print(vehicle.location.global_frame.alt)
    print("Changing to Landing mode")
    vehicle.mode = VehicleMode("LAND")
    time.sleep(10);
    print("Changing to RTL mode")
    vehicle.mode = VehicleMode("RTL")

# Main Mission
try:
    # Fetch the home location using GPS
    home_lat, home_lon = get_home_location()
    #hom_lat ,home_lon = 12.9832062, 80.0409941
    home_alt = 10 # Altitude in meters for home (just for logging, not used in the flight)

    # Define the hardcoded destination location (latitude, longitude, altitude)
    destination_lat = 12.971499 # Example latitude (destination)
    destination_lon = 80.044081 # Example longitude (destination)
    target_altitude = 10 # Altitude in meters

    print(f"Home Location: Latitude={home_lat}, Longitude={home_lon}, Altitude={home_alt}")
    print(f"Destination Location: Latitude={destination_lat}, Longitude={destination_lon}, Altitude={target_altitude}")

    arm_and_takeoff(target_altitude)  # Take off to target altitude
    fly_to_destination_Alt(destination_lat, destination_lon, target_altitude)  # Fly to hardcoded destination
    if vehicle.mode.name != "RTL" :
        disarm_and_task_alt()# Land at the destination and RTL

finally:
    print("Closing vehicle connection...")
    vehicle.close()
