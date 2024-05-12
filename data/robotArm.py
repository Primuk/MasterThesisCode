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
import json
import csv
from datetime import datetime, timedelta

def generate_sensor_data(num_samples):
    data = []
    current_time = datetime.now()
    
    for _ in range(num_samples):
        sample_data = {
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
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
        data.append(sample_data)
        current_time += timedelta(seconds=1)
    
    return data

def main():
    num_samples = 1000  # Number of samples to generate
    sensor_data = generate_sensor_data(num_samples)

    # Save data in CSV format
    with open('data/robot_sensor_data.csv', 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=sensor_data[0].keys())
        writer.writeheader()
        writer.writerows(sensor_data)

if __name__ == "__main__":
    main()
