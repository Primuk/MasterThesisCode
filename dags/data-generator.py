from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator
import os

# Define the default arguments for the DAG
default_args = {
    'owner': 'Primula',
    'depends_on_past': False,
    'start_date': datetime(2024, 5, 15),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    dag_id='data-simulator',
    default_args=default_args,
    description='Generate sample data daily runs for 10 mins to simulate IoT devices',
    schedule_interval='@daily',
    catchup=False
)

# Define the command to run the data generation script
script_path = "/app/data/robotArm.py"
generate_data_command = 'python {}'.format(script_path)

# Define the command to activate virtual environment and install dependencies
activate_venv_command = 'source /app/env/bin/activate && pip install -r /app/requirements.txt'

# Define the task to activate virtual environment and install dependencies
activate_venv_task = BashOperator(
    task_id='setup_environment',
    bash_command=activate_venv_command,
    dag=dag
)

# Define the task to generate data daily
generate_data_task = BashOperator(
    task_id='generate_data',
    bash_command=generate_data_command,
    dag=dag
)

# Define the path to the Kafka producer script
kafka_producer_command = 'cd /app/scripts && python create_topic_send_robodata.py'

# Define the task to start Kafka producer
start_kafka_producer_task = BashOperator(
    task_id='start_kafka_producer',
    bash_command=kafka_producer_command,
    dag=dag
)

# task to stop the DAG after 10 minutes
def stop_dag(**context):
    print("Stopping DAG after 10 minutes...")
    os.kill(os.getpid(), 9)

stop_dag_task = PythonOperator(
    task_id='stop_dag',
    python_callable=stop_dag,
    dag=dag
)

# Set task dependencies
activate_venv_task >> [generate_data_task, start_kafka_producer_task] >> stop_dag_task