#!/usr/bin/env python

"""

    Make sample time series data.

"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json,os

def main():

    current_date = datetime.now()
    start_of_current_day = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_next_day = start_of_current_day + timedelta(days=1)
    date_rng = pd.date_range(start=start_of_current_day, end=start_of_next_day, freq='s')
    df = pd.DataFrame(date_rng, columns=['timestamp'])

    # Generating random values for position, velocity, acceleration, pressure, and temperature
    
    np.random.seed(42)
    df['sensor'] = np.random.choice(['sensor1', 'sensor2', 'sensor3'], size=len(date_rng))
    df['position_x'] = np.random.uniform(-10, 10, size=len(date_rng))  # X-axis position
    df['position_y'] = np.random.uniform(-10, 10, size=len(date_rng))  # Y-axis position
    df['velocity_x'] = np.random.uniform(-1, 1, size=len(date_rng))  # X-axis velocity
    df['velocity_y'] = np.random.uniform(-1, 1, size=len(date_rng))  # Y-axis velocity
    df['acceleration_x'] = np.random.uniform(-0.1, 0.1, size=len(date_rng))  # X-axis acceleration
    df['acceleration_y'] = np.random.uniform(-0.1, 0.1, size=len(date_rng))  # Y-axis acceleration
    df['pressure'] = np.random.uniform(900, 1100, size=len(date_rng))  # Atmospheric pressure (in hPa)
    df['temperature'] = np.random.uniform(20, 30, size=len(date_rng))  # Temperature (in Celsius)
    
    more_details = []
    for _ in range(len(date_rng)):
        detail = {
            "value1": "Sample additional info",
            "value2": "Sample attribute value"
        }
        more_details.append(json.dumps(detail))

    df['more_details'] = more_details

    df = df.sort_values(by=['timestamp'])
    script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory of the script
    output_path = os.path.join(script_dir, 'data.csv')  # Construct the absolute path to data.csv
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
