from pyspark.context import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
import json

neo4j_url = "bolt://host.docker.internal:7687"
neo4j_user = "neo4j"
neo4j_password = "12345678"

# Create SparkContext and SparkSession
spark = SparkSession \
    .builder \
    .appName('Data science workflow with Neo4j and Spark') \
    .config('spark.jars.packages', 'org.neo4j:neo4j-connector-apache-spark_2.13:5.3.0_for_spark_3') \
    .config("neo4j.url", neo4j_url) \
    .config("neo4j.authentication.type", "basic") \
    .config("neo4j.authentication.basic.username", neo4j_user) \
    .config("neo4j.authentication.basic.password", neo4j_password) \
    .master('local[*]') \
    .getOrCreate()

# Define Kafka topic name
TOPIC_NAME = 'DATA_STREAM'

# Define schema for JSON data
schema_forJson = StructType([
    StructField("more_details", StringType(), True),
    StructField("position_x", StringType(), True),
    StructField("position_y", StringType(), True),
    StructField("acceleration_y", StringType(), True),
    StructField("acceleration_x", StringType(), True),
    StructField("temperature", StringType(), True),
    StructField("sensor", StringType(), True),
    StructField("pressure", StringType(), True),
    StructField("velocity_x", StringType(), True),
    StructField("velocity_y", StringType(), True),
    StructField("timestamp", StringType(), True)
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

# Apply appropriate data types to df_parsed
df_parsed = df_parsed.select(
    col("more_details").cast(StringType()).alias("more_details"),
    col("position_x").cast(DoubleType()).alias("position_x"),
    col("position_y").cast(DoubleType()).alias("position_y"),
    col("acceleration_y").cast(DoubleType()).alias("acceleration_y"),
    col("acceleration_x").cast(DoubleType()).alias("acceleration_x"),
    col("temperature").cast(DoubleType()).alias("temperature"),
    col("sensor").cast(StringType()).alias("sensor"),
    col("pressure").cast(DoubleType()).alias("pressure"),
    col("velocity_x").cast(DoubleType()).alias("velocity_x"),
    col("velocity_y").cast(DoubleType()).alias("velocity_y"),
    col("timestamp").cast(TimestampType()).alias("timestamp")
)

query = df_parsed.writeStream \
    .format("org.neo4j.spark.DataSource") \
    .option("save.mode", "ErrorIfExists") \
    .option("checkpointLocation", "/neo4j_checkpoint") \
    .option("labels", "sensor") \
    .start() \
    .awaitTermination()