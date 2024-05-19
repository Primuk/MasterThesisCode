from pyspark.context import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType,TimestampType
import json

sc = SparkContext('local')
spark = SparkSession(sc)

TOPIC_NAME = 'DATA_STREAM'

schema_forJson= StructType([
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
    # Decode binary data to string using UTF-8 decoding
    decoded_str = value.decode('utf-8')
    # Parse the JSON string
    #parsed_json = json.loads(decoded_str)
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
df_parsed = df_parsed.select("parsed_value")
# Apply from_json to parse the JSON string into a struct column
df_parsed1 = df_parsed \
    .select(F.from_json(df_parsed.parsed_value, schema_forJson).alias('parsed_value1')) \
    .select(F.col('parsed_value1.*'))

# Apply from_json to parse the JSON string into a struct column
df_parsed = df_parsed.withColumn("parsed_value_struct", from_json(col("parsed_value"), schema_forJson))

# Apply appropriate data types to df_parsed
# Select individual fields from the struct column and cast them to appropriate data types
df_parsed = df_parsed.select(
    col("parsed_value_struct.more_details").cast(StringType()).alias("more_details"),
    col("parsed_value_struct.position_x").cast(DoubleType()).alias("position_x"),
    col("parsed_value_struct.position_y").cast(DoubleType()).alias("position_y"),
    col("parsed_value_struct.acceleration_y").cast(DoubleType()).alias("acceleration_y"),
    col("parsed_value_struct.acceleration_x").cast(DoubleType()).alias("acceleration_x"),
    col("parsed_value_struct.temperature").cast(DoubleType()).alias("temperature"),
    col("parsed_value_struct.sensor").cast(StringType()).alias("sensor"),
    col("parsed_value_struct.pressure").cast(DoubleType()).alias("pressure"),
    col("parsed_value_struct.velocity_x").cast(DoubleType()).alias("velocity_x"),
    col("parsed_value_struct.velocity_y").cast(DoubleType()).alias("velocity_y"),
    col("parsed_value_struct.timestamp").cast(TimestampType()).alias("timestamp")
)

# Select individual fields from the struct column
df_parsed = df_parsed.select(
    "more_details",
    "position_x",
    "position_y",
    "acceleration_y",
    "acceleration_x",
    "temperature",
    "sensor",
    "pressure",
    "velocity_x",
    "velocity_y",
    "timestamp"
)

# Write the streaming DataFrame to a directory
query = df_parsed\
    .writeStream \
    .outputMode("append") \
    .trigger(processingTime="15 seconds") \
    .format("parquet") \
    .option("path", "./test") \
    .option("checkpointLocation", "./checkpoint") \
    .start()
# Await termination (or use any other desired method to start the query)
query.awaitTermination()