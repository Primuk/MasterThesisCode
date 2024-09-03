import csv
import json
import time
import datetime
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic

admin_client = KafkaAdminClient(bootstrap_servers="172.25.0.12:9092")
producer = KafkaProducer(bootstrap_servers='172.25.0.13:9092', 
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

TOPIC_NAME = 'ROBOT_STREAM_ONTO'

existing_topics = admin_client.list_topics()

if TOPIC_NAME not in existing_topics:
    topic_list = [NewTopic(name=TOPIC_NAME, num_partitions=6, replication_factor=1)]
    admin_client.create_topics(new_topics=topic_list, validate_only=False)

start_time = datetime.datetime.now()
elapsed_time = datetime.timedelta(seconds=0)

while elapsed_time < datetime.timedelta(minutes=20):
    with open('../data/robot_sensor_data_validated.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = row['joint_name'].encode('utf-8')  
            producer.send(TOPIC_NAME, key=key, value=row)
            producer.flush()
        time.sleep(2)  # Waits for 5 seconds to read new data
        elapsed_time = datetime.datetime.now() - start_time

producer.close()