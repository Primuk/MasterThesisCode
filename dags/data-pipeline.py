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
# Define the command to stream spark to neo4j and staging
spark_to_neo4j_command = 'spark-submit \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.5,org.neo4j:neo4j-connector-apache-spark_2.11:4.1.5_for_spark_2.4 \
    --jars /app/kafka-clients-2.2.0.jar,/app/neo4j-connector-apache-spark_2.11-4.1.5_for_spark_2.4.jar \
    --driver-class-path /app/kafka-clients-2.2.0.jar \
    /app/scripts/spark-to-neo4j-robo.py'

# Define the task to execute deploy.sh
ingestion_task = BashOperator(
    task_id='data_ingestion_for_staging_and_neo4j',
    bash_command=spark_to_neo4j_command,
    dag=dag,
    xcom_push=False
)
hdfs_to_neo4j_command =  'spark-submit \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.5,org.neo4j:neo4j-connector-apache-spark_2.11:4.1.5_for_spark_2.4 \
    --jars /app/kafka-clients-2.2.0.jar,/app/neo4j-connector-apache-spark_2.11-4.1.5_for_spark_2.4.jar \
    --driver-class-path /app/kafka-clients-2.2.0.jar \
    /app/scripts/spark-aggregator.py'


aggregation_task = BashOperator(
    task_id='aggregation_task_to_neo4j',
    bash_command=hdfs_to_neo4j_command,
    dag=dag,
    xcom_push=False
)

# Set task dependencies
deploy_task >> [ingestion_task, aggregation_task]
#deploy_task >> [ingestion_task]
