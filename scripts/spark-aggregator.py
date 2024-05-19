from pyspark.sql import SparkSession
from pyspark.sql.functions import window, min, max, col, avg, udf,lag, when,lit
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
from pyspark.sql.window import Window
import logging

# Initialize SparkSession
spark = SparkSession.builder \
    .appName("Streaming Aggregation and Neo4j Update") \
    .getOrCreate()

# Define the schema for reading data from HDFS
schema_read = StructType([
    StructField("timestamp", TimestampType(), True),
    StructField("load", DoubleType(), True),
    StructField("velocity", DoubleType(), True),
    StructField("temperature", DoubleType(), True),
    StructField("pressure", DoubleType(), True),
    StructField("gripper_status", StringType(), True),
    StructField("proximity", StringType(), True),
    StructField("position", StructType([
        StructField("x", DoubleType(), True),
        StructField("y", DoubleType(), True),
        StructField("z", DoubleType(), True)
    ]), True),
    StructField("joint_angles", StructType([
        StructField("joint_1", DoubleType(), True),
        StructField("joint_2", DoubleType(), True),
        StructField("joint_3", DoubleType(), True),
        StructField("joint_4", DoubleType(), True),
        StructField("joint_5", DoubleType(), True),
        StructField("joint_6", DoubleType(), True)
    ]), True),
    StructField("force_x", DoubleType(), True),
    StructField("force_y", DoubleType(), True),
    StructField("force_z", DoubleType(), True),
    StructField("torque_x", DoubleType(), True),
    StructField("torque_y", DoubleType(), True),
    StructField("torque_z", DoubleType(), True)
])

# Read streaming data from HDFS
streaming_df = spark.readStream \
    .schema(schema_read) \
    .format("parquet") \
    .load("/app/staging")

# Calculate min and max temperatures over a 5-minute window
result_df = streaming_df \
    .withWatermark("timestamp", "5 minutes") \
    .groupBy(window("timestamp", "5 minutes")) \
    .agg(min("temperature").alias("min_temperature"), max("temperature").alias("max_temperature"),
         avg("temperature").alias("avg_temperature"))

result_df = result_df.withColumn(
    "status", 
    when(50 < col("avg_temperature"), "ALERT").otherwise("NORMAL")
)
#Set property of those nodes as status "Normal" or alert in neo4j for those having timestamp in the same window
#TODO

# Display the result
query = result_df.writeStream \
    .outputMode("complete") \
    .format("console") \
    .start()

query.awaitTermination()
query.stop()