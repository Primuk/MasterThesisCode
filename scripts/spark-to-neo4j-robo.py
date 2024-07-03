from pyspark.sql.session import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
from pyspark.sql import functions as F
import logging
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

neo4j_url = "bolt://host.docker.internal:7687"
neo4j_user = "neo4j"
neo4j_password = "12345678"

# Creating SparkSession
spark = SparkSession.builder \
    .appName("Read from Kafka and Parse JSON") \
    .config('spark.jars.packages', 'org.neo4j:neo4j-connector-apache-spark_2.11-4.1.5_for_spark_2.4.jar') \
    .config("spark.jars.repositories", "https://repo1.maven.org/maven2") \
    .config("neo4j.url", neo4j_url) \
    .config("neo4j.authentication.type", "basic") \
    .config("neo4j.authentication.basic.username", neo4j_user) \
    .config("neo4j.authentication.basic.password", neo4j_password) \
    .master('local[*]') \
    .getOrCreate()

# Define Kafka topic name
TOPIC_NAME = 'ROBOT_STREAM_ONTO'

# Define schema for JSON data
schema_forJson = StructType([
    StructField("timestamp", StringType(), True),
    StructField("position", StringType(), True),
    StructField("force_torque", StringType(), True),
    StructField("joint_angles", StringType(), True),
    StructField("velocity", StringType(), True),
    StructField("current", StringType(), True),
    StructField("environment", StringType(), True),
    StructField("log", StringType(), True)
])

# Define a function to decode and parse the JSON string
def decode_and_parse(value):
    decoded_str = value.decode('utf-8')
    return decoded_str

# Register the function as a UDF (User Defined Function)
decode_and_parse_udf = udf(decode_and_parse, StringType())

# Read from Kafka as a streaming DataFrame
df1 = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "172.25.0.12:9092,172.25.0.13:9092") \
    .option("subscribe", TOPIC_NAME) \
    .load()

# Apply the UDF to decode and parse the value column
df_parsed = df1.withColumn("parsed_value", decode_and_parse_udf(col("value")))

# Apply from_json to parse the JSON string into a struct column
df_parsed = df_parsed \
    .select(F.from_json(df_parsed.parsed_value, schema_forJson).alias('parsed_value1')) \
    .select(F.col('parsed_value1.*'))

# Define schema for nested JSON columns
schema_position = StructType([
    StructField("x", DoubleType(), True),
    StructField("y", DoubleType(), True),
    StructField("z", DoubleType(), True)
])

schema_force_torque = StructType([
    StructField("force", StructType([
        StructField("x", DoubleType(), True),
        StructField("y", DoubleType(), True),
        StructField("z", DoubleType(), True)
    ]), True),
    StructField("torque", StructType([
        StructField("x", DoubleType(), True),
        StructField("y", DoubleType(), True),
        StructField("z", DoubleType(), True)
    ]), True)
])

schema_joint_angles = StructType([
    StructField("joint_1", DoubleType(), True),
    StructField("joint_2", DoubleType(), True),
    StructField("joint_3", DoubleType(), True),
    StructField("joint_4", DoubleType(), True),
    StructField("joint_5", DoubleType(), True),
    StructField("joint_6", DoubleType(), True)
])

schema_environment = StructType([
    StructField("air_quality", StringType(), True),
    StructField("humidity", StringType(), True),
    StructField("temperature", StringType(), True)
])

schema_log = StructType([
    StructField("timestamp", StringType(), True),
    StructField("type", StringType(), True),
    StructField("message", StringType(), True)
])

# Parse nested JSON columns
df_parsed = df_parsed.withColumn("position", F.from_json("position", schema_position))
df_parsed = df_parsed.withColumn("force_torque", F.from_json("force_torque", schema_force_torque))
df_parsed = df_parsed.withColumn("joint_angles", F.from_json("joint_angles", schema_joint_angles))
df_parsed = df_parsed.withColumn("environment", F.from_json("environment", schema_environment))
df_parsed = df_parsed.withColumn("log", F.from_json("log", schema_log))

# Flatten force_torque column
df_parsed = df_parsed.withColumn("force_x", F.col("force_torque.force.x")) \
                     .withColumn("force_y", F.col("force_torque.force.y")) \
                     .withColumn("force_z", F.col("force_torque.force.z")) \
                     .withColumn("torque_x", F.col("force_torque.torque.x")) \
                     .withColumn("torque_y", F.col("force_torque.torque.y")) \
                     .withColumn("torque_z", F.col("force_torque.torque.z"))

# Drop the original force_torque column
df_parsed = df_parsed.drop("force_torque")
# Flatten log column
df_parsed = df_parsed.withColumn("environment_AirQuality", F.col("environment.air_quality")) \
                     .withColumn("environment_humidity", F.col("environment.humidity")) \
                     .withColumn("environment_Temperature", F.col("environment.temperature"))
# Drop the original environment column
df_parsed = df_parsed.drop("environment")

# Flatten log column
df_parsed = df_parsed.withColumn("log_timestamp", F.col("log.timestamp")) \
                     .withColumn("log_type", F.col("log.type")) \
                     .withColumn("log_message", F.col("log.message"))

# Drop the original log column
df_parsed = df_parsed.drop("log")

# Typecast columns to correct data types
df_parsed = df_parsed.withColumn("timestamp", col("timestamp").cast(TimestampType())) \
                     .withColumn("velocity", col("velocity").cast(DoubleType())) \
                     .withColumn("current", col("current").cast(DoubleType())) 

def process_batch(batch_df, batch_id):
    # Count entries in the batch
    count = batch_df.count()
    logger.info("Batch {0} has {1} entries.".format(batch_id, count))
    
    # Filter out duplicates based on timestamp
    deduplicated_df = batch_df.dropDuplicates(["timestamp"])
    
    query = """
    
    """

    # Write the DataFrame to Neo4j using the Cypher query
    deduplicated_df.write \
        .format("org.neo4j.spark.DataSource") \
        .option("query", query) \
        .mode("Overwrite") \
        .option("url", neo4j_url) \
        .option("authentication.basic.username", neo4j_user) \
        .option("authentication.basic.password", neo4j_password) \
        .save()
    # # Write data to Neo4j
    # deduplicated_df.write \
    #     .format("org.neo4j.spark.DataSource") \
    #     .mode("append") \
    #     .option("url", neo4j_url) \
    #     .option("authentication.basic.username", neo4j_user) \
    #     .option("authentication.basic.password", neo4j_password) \
    #     .option("labels", ":RobotData") \
    #     .option("node.keys", "timestamp") \
    #     .save()

# Write the parsed data to Neo4j and count entries in each batch
query = df_parsed.writeStream \
    .outputMode("append") \
    .foreachBatch(process_batch) \
    .start()

# Wait for the query to terminate
query.awaitTermination()
