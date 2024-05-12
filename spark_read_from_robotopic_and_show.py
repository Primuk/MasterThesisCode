from pyspark.sql.session import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql.types import StructType, StructField, StringType, DoubleType,TimestampType
from pyspark.context import SparkContext
from pyspark.sql import functions as F
import json

# Creating SparkSession
sc = SparkContext('local')
sc.setLogLevel("ERROR")
spark = SparkSession(sc).builder \
    .appName("Read from Kafka and Parse JSON") \
    .getOrCreate()

# Define Kafka topic name
TOPIC_NAME = 'ROBOT1_STREAM'

# Define schema for JSON data
schema_forJson = StructType([
    StructField("force_torque",StringType(), True),
    StructField("timestamp", TimestampType(), True),
    StructField("position", StringType(), True),
    StructField("load", StringType(), True),
    StructField("velocity", StringType(), True),
    StructField("temperature", StringType(), True),
    StructField("pressure", StringType(), True),
    StructField("gripper_status", StringType(), True),
    StructField("proximity", StringType(), True),
    StructField("joint_angles", StringType(), True)
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
df_parsed.printSchema()
# Show the DataFrame with parsed columns
#df_parsed.show(truncate=False)
# Define schema for force_torque JSON
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

# Apply from_json to parse the force_torque JSON string into a struct column
df_parsed = df_parsed.withColumn("force_torque_parsed", F.from_json("force_torque", schema_force_torque))

# Define schema for position JSON
schema_position = StructType([
    StructField("x", DoubleType(), True),
    StructField("y", DoubleType(), True),
    StructField("z", DoubleType(), True)
])

# Apply from_json to parse the position JSON string into a struct column
df_parsed = df_parsed.withColumn("position_parsed", F.from_json("position", schema_position))

# Define schema for joint_angles JSON
schema_joint_angles = StructType([
    StructField("joint_1", DoubleType(), True),
    StructField("joint_2", DoubleType(), True),
    StructField("joint_3", DoubleType(), True),
    StructField("joint_4", DoubleType(), True),
    StructField("joint_5", DoubleType(), True),
    StructField("joint_6", DoubleType(), True)
])

# Apply from_json to parse the joint_angles JSON string into a struct column
df_parsed = df_parsed.withColumn("joint_angles_parsed", F.from_json("joint_angles", schema_joint_angles))

# Drop the original JSON columns
df_parsed = df_parsed.drop("force_torque", "position", "joint_angles")

# Rename the parsed columns
df_parsed = df_parsed \
    .withColumnRenamed("force_torque_parsed", "force_torque") \
    .withColumnRenamed("position_parsed", "position") \
    .withColumnRenamed("joint_angles_parsed", "joint_angles")

# Show the schema
df_parsed.printSchema()

"""
# Write the streaming DataFrame to console
query = df_parsed \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

# Wait for termination
query.awaitTermination()
"""