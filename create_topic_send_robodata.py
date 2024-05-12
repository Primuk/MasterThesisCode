import csv
import json
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic

admin_client = KafkaAdminClient(bootstrap_servers="172.25.0.12:9092")
producer = KafkaProducer(bootstrap_servers='172.25.0.13:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

TOPIC_NAME = 'ROBOT1_STREAM'

existing_topics = admin_client.list_topics()

if TOPIC_NAME not in existing_topics:
    topic_list = [NewTopic(name=TOPIC_NAME, num_partitions=1, replication_factor=1)]
    admin_client.create_topics(new_topics=topic_list, validate_only=False)

# Read data from CSV file and send each row as JSON to Kafka
with open('data/robot_sensor_data.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        producer.send(TOPIC_NAME, value=row)

producer.flush()
producer.close()
