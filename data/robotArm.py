#!/usr/bin/env python

"""

    Generate sample data from various sensors on a robot arm.

    Sensors and corresponding columns:
    - Position:
        - x: X-coordinate position
        - y: Y-coordinate position
        - z: Z-coordinate position

    - Force/Torque:
        - force:
            - x: Force along the X-axis
            - y: Force along the Y-axis
            - z: Force along the Z-axis
        - torque:
            - x: Torque around the X-axis
            - y: Torque around the Y-axis
            - z: Torque around the Z-axis

    - Joint Angles:
        - joint_1 to joint_6: Angles of the robot arm's joints

    - Velocity: Velocity of the robot arm

    - Temperature: Temperature measurement

    - Pressure: Pressure measurement

    - Proximity: Proximity sensor status (near or far)

    - Gripper Status: Status of the gripper (open or closed)

    - Load: Load being carried by the robot arm's end-effector

"""
import numpy as np
import csv
from datetime import datetime, timedelta
import time,os

def generate_sensor_data(interval):
    script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory of the script
    output_path = os.path.join(script_dir, 'robot_sensor_data1.csv')  # Construct the absolute path to data.csv

    while True:
        sample_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'position': {
                'x': np.random.uniform(-10, 10),
                'y': np.random.uniform(-10, 10),
                'z': np.random.uniform(0, 20)
            },
            'force_torque': {
                'force': {
                    'x': np.random.uniform(-50, 50),
                    'y': np.random.uniform(-50, 50),
                    'z': np.random.uniform(-50, 50)
                },
                'torque': {
                    'x': np.random.uniform(-10, 10),
                    'y': np.random.uniform(-10, 10),
                    'z': np.random.uniform(-10, 10)
                }
            },
            'joint_angles': {
                'joint_1': np.random.uniform(-180, 180),
                'joint_2': np.random.uniform(-180, 180),
                'joint_3': np.random.uniform(-180, 180),
                'joint_4': np.random.uniform(-180, 180),
                'joint_5': np.random.uniform(-180, 180),
                'joint_6': np.random.uniform(-180, 180)
            },
            'velocity': np.random.uniform(0, 5),
            'temperature': np.random.uniform(0, 100),
            'pressure': np.random.uniform(800, 1200),
            'proximity': np.random.choice(['near', 'far']),
            'gripper_status': np.random.choice(['open', 'closed']),
            'load': np.random.uniform(0, 100)
        }

        with open(output_path, 'a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=sample_data.keys())
            if csv_file.tell() == 0:
                writer.writeheader()
            writer.writerow(sample_data)

        time.sleep(interval)

def main():
    interval_seconds = 1  # Interval between samples in seconds
    generate_sensor_data(interval_seconds)

if __name__ == "__main__":
    main()