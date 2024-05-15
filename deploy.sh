#!/bin/bash

# Activate the virtual environment
source /app/env/bin/activate

# Install dependencies from requirements.txt
pip install -r /app/requirements.txt

# Navigate to the project directory
cd /app 