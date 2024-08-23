import numpy as np
import csv
from datetime import datetime
import time
import os
import json
import rdflib
import random

def extract_constraints(ontology_path):
    g = rdflib.Graph()
    g.parse(ontology_path, format='ttl')

    constraints = {}

    query = """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX : <http://example.org/robotics#>
    
    SELECT ?property ?min ?max
    WHERE {
        ?class rdfs:subClassOf ?restriction .
        ?restriction owl:onProperty ?property ;
                     owl:allValuesFrom ?range .
        ?range owl:onDatatype ?datatype ;
               owl:withRestrictions ?restrictions .
        ?restrictions rdf:rest*/rdf:first ?restrictionItem .
        OPTIONAL { ?restrictionItem xsd:minInclusive ?min }
        OPTIONAL { ?restrictionItem xsd:maxInclusive ?max }
    }
    """

    results = g.query(query)

    for row in results:
        property_uri = str(row.property)
        property_name = property_uri.split('#')[-1]
        min_val = float(row.min) if row.min is not None else None
        max_val = float(row.max) if row.max is not None else None

        if property_name not in constraints:
            constraints[property_name] = {}

        if min_val is not None:
            constraints[property_name]['min'] = min_val
        if max_val is not None:
            constraints[property_name]['max'] = max_val

    return constraints

def generate_sensor_data(interval, constraints):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    output_path = os.path.join(script_dir, 'robot_sensor_data_validated.csv')
    time_step = 0

    joint_names = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']
    joint_functions = [
        lambda t: np.clip(45 * np.sin(t), constraints.get('hasJointAngle', {}).get('min', -360), constraints.get('hasJointAngle', {}).get('max', 360)),
        lambda t: np.clip(30 * np.sin(t / 2), constraints.get('hasJointAngle', {}).get('min', -360), constraints.get('hasJointAngle', {}).get('max', 360)),
        lambda t: np.clip(15 * np.cos(t / 3), constraints.get('hasJointAngle', {}).get('min', -360), constraints.get('hasJointAngle', {}).get('max', 360)),
        lambda t: np.clip(10 * np.sin(t / 4), constraints.get('hasJointAngle', {}).get('min', -360), constraints.get('hasJointAngle', {}).get('max', 360)),
        lambda t: np.clip(20 * np.cos(t / 5), constraints.get('hasJointAngle', {}).get('min', -360), constraints.get('hasJointAngle', {}).get('max', 360)),
        lambda t: np.clip(25 * np.sin(t / 6), constraints.get('hasJointAngle', {}).get('min', -360), constraints.get('hasJointAngle', {}).get('max', 360))
    ]

    while True:
        for joint_index in range(len(joint_names)):
            joint_name = joint_names[joint_index]
            joint_angle = joint_functions[joint_index](time_step)

            # Simulate position based on joint angles (simplified kinematics)
            position = {
                'x': np.cos(np.radians(joint_angle)),
                'y': np.sin(np.radians(joint_angle)),
                'z': np.sin(np.radians(joint_angle)) / 2
            }

            # Simulate force and torque with constraints
            force_torque = {
                'force': {
                    'x': np.clip(position['x'] * 10, -constraints.get('hasForce', {}).get('max', 30), constraints.get('hasForce', {}).get('max', 30)),
                    'y': np.clip(position['y'] * 10, -constraints.get('hasForce', {}).get('max', 30), constraints.get('hasForce', {}).get('max', 30)),
                    'z': np.clip(position['z'] * 10, -constraints.get('hasForce', {}).get('max', 30), constraints.get('hasForce', {}).get('max', 30))
                },
                'torque': {
                    'x': np.clip(joint_angle * 0.1, -constraints.get('hasTorque', {}).get('max', 10), constraints.get('hasTorque', {}).get('max', 10)),
                    'y': np.clip(joint_angle * 0.1, -constraints.get('hasTorque', {}).get('max', 10), constraints.get('hasTorque', {}).get('max', 10)),
                    'z': np.clip(joint_angle * 0.1, -constraints.get('hasTorque', {}).get('max', 10), constraints.get('hasTorque', {}).get('max', 10))
                }
            }

            # Simulate current (in amperes) as a function of force
            current = np.clip(np.sqrt(np.sum(np.array(list(force_torque['force'].values()))**2)) * 0.1, constraints.get('hasCurrent', {}).get('min', 2.5), constraints.get('hasCurrent', {}).get('max', 25))

            # Simulate velocity based on joint angle changes
            velocity = np.sqrt(position['x']**2 + position['y']**2) * 0.1

            # Environment sensors with constraints
            environment = {
                'temperature': np.clip(25 + 5 * np.sin(time_step / 10), constraints.get('hasTemperature', {}).get('min', 0), constraints.get('hasTemperature', {}).get('max', 50)),
                'humidity': np.clip(50 + 10 * np.sin(time_step / 15), 0, constraints.get('hasHumidity', {}).get('max', 90)),
                'air_quality': np.random.choice(['Good', 'Moderate', 'Unhealthy'], p=[0.7, 0.2, 0.1])
            }

            # Log type and message
            log_type = np.random.choice(['warn', 'info'], p=[0.4, 0.6])
            log_message = {
                'warn': 'Warning log message',
                'info': 'Info log message'
            }[log_type]

            # Introduce errors randomly
            if random.random() < 0.01:  # 1% chance of a spike error
                joint_angle = random.choice([360, -360])  # Spike to extreme value
                log_type = 'error'
                log_message = 'Error log message'
                force_torque['force']['x'] = constraints.get('hasForce', {}).get('max', 30) + 10  # Out-of-bounds force
                force_torque['torque']['y'] = constraints.get('hasTorque', {}).get('max', 10) + 5  # Out-of-bounds torque
                environment['air_quality'] = 'Unhealthy'

            # Package data
            sample_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sensor_name': '{}_sensor'.format(joint_name),
                'joint_name': joint_name,
                'position': position,
                'force_torque': force_torque,
                'joint_angle': joint_angle,
                'velocity': velocity,
                'current': current,
                'environment': environment,
                'log': {
                    'type': log_type,
                    'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'message': log_message
                }
            }

            # Write to CSV
            with open(output_path, 'a', newline='') as csv_file:
                fieldnames = ['timestamp', 'sensor_name', 'joint_name', 'position', 'force_torque', 'joint_angle', 'velocity', 'current', 'environment', 'log']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                if csv_file.tell() == 0:
                    writer.writeheader()
                
                json_data = {key: json.dumps(value) if isinstance(value, dict) else value for key, value in sample_data.items()}
                writer.writerow(json_data)

            time_step += 0.1
            time.sleep(interval)
            if time_step >= 200:  # runs for 10 mins
                break
        if time_step >= 200:
            break

def main():
    ontology_path = '/app/ontology/sensor1_KB.ttl'  # Directly set the correct path to the ontology file
    constraints = extract_constraints(ontology_path)
    interval_seconds = 1
    generate_sensor_data(interval_seconds, constraints)

if __name__ == "__main__":
    main()
