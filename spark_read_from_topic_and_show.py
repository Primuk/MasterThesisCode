from pyspark.context import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.sql.functions import col, from_json,udf, explode
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
import json
sc = SparkContext('local')
spark = SparkSession(sc)

TOPIC_NAME = 'DATA_STREAM'
df1 = spark \
    .read \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "172.25.0.12:9092,172.25.0.13:9092") \
    .option("startingOffsets", "earliest") \
    .option("subscribe", TOPIC_NAME) \
    .load()
df1.show()

# Define a function to decode and parse the JSON string
def decode_and_parse(value):
    # Decode binary data to string using UTF-8 decoding
    decoded_str = value.decode('utf-8')
    # Parse the JSON string
    parsed_json = json.loads(decoded_str)
    return parsed_json

# Register the function as a UDF (User Defined Function)
decode_and_parse_udf = udf(decode_and_parse, StringType())

# Apply the UDF to decode and parse the value column
df_parsed = df1.withColumn("parsed_value", decode_and_parse_udf(col("value")))

schema = StructType([
    StructField("acceleration_x", StringType(), True),
    StructField("sensor", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("position_y", StringType(), True),
    StructField("velocity_x", StringType(), True),
    StructField("temperature", StringType(), True),
    StructField("more_details", StringType(), True),
    StructField("acceleration_y", StringType(), True),
    StructField("pressure", StringType(), True),
    StructField("position_x", StringType(), True),
    StructField("velocity_y", StringType(), True)
])

# Apply from_json to parse the JSON string into a struct column
df_parsed = df_parsed.withColumn("parsed_value_struct", from_json(col("parsed_value"), schema))

# Select individual fields from the struct column
df_parsed = df_parsed.select(
    "parsed_value_struct.acceleration_x",
    "parsed_value_struct.sensor",
    "parsed_value_struct.timestamp",
    "parsed_value_struct.position_y",
    "parsed_value_struct.velocity_x",
    "parsed_value_struct.temperature",
    "parsed_value_struct.more_details",
    "parsed_value_struct.acceleration_y",
    "parsed_value_struct.pressure",
    "parsed_value_struct.position_x",
    "parsed_value_struct.velocity_y"
)

# Show the DataFrame with parsed columns
df_parsed.show(truncate=False)
