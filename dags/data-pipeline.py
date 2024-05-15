from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

# Define the default arguments for the DAG
default_args = {
    'owner': 'Primula',
    'depends_on_past': False,
    'start_date': datetime(2024, 5, 14),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    dag_id='Data-Pipeline',
    default_args=default_args,
    description='End-to-end pipeline for real-time processing and knowledge graph',
    schedule_interval=None,  # You can set the schedule_interval as needed
    catchup=False
)

# Define the command to execute deploy.sh
deploy_command = '/app/deploy.sh '

# Define the task to execute deploy.sh
deploy_task = BashOperator(
    task_id='build_environment',
    bash_command=deploy_command,
    dag=dag,
    xcom_push=False
)

# Define the path to the Kafka producer script
kafka_producer_command = 'cd /app/scripts && python create_topic_send_robodata.py'

# Define the task to start Kafka producer
kafka_producer_task = BashOperator(
    task_id='start_kafka_producer',
    bash_command=kafka_producer_command,
    dag=dag
)

# Set task dependencies
deploy_task >> kafka_producer_task
