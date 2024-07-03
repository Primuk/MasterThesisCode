from pyspark.sql import SparkSession
from pyspark.sql.functions import window, min, max, col, avg, when
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
from neo4j import GraphDatabase

# Initialize SparkSession
spark = SparkSession.builder \
    .appName("Streaming Aggregation and Neo4j Update") \
    .getOrCreate()

# Define the schema for reading data from HDFS
schema_read = StructType([
    StructField("timestamp", TimestampType(), True),
    StructField("velocity", DoubleType(), True),
    StructField("current", DoubleType(), True),
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
    StructField("torque_z", DoubleType(), True),
    StructField("environment", StructType([
        StructField("temperature", DoubleType(), True),
        StructField("humidity", DoubleType(), True),
        StructField("air_quality", StringType(), True)
    ]), True),
    StructField("log", StructType([
        StructField("type", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("message", StringType(), True)
    ]), True)
])

# Read streaming data from HDFS
streaming_df = spark.readStream \
    .schema(schema_read) \
    .format("parquet") \
    .load("/app/staging")

# Calculate min, max, and average temperatures over a 5-minute window
result_df = streaming_df \
    .withWatermark("timestamp", "5 minutes") \
    .groupBy(window("timestamp", "5 minutes")) \
    .agg(min("environment.temperature").alias("min_temperature"), 
         max("environment.temperature").alias("max_temperature"),
         avg("environment.temperature").alias("avg_temperature"))

result_df = result_df.withColumn(
    "status", 
    when(col("avg_temperature") > 30, "ALERT").otherwise("NORMAL")
)

# Define a function to update the status in Neo4j
def update_neo4j_status(rows):
    neo4j_url = "bolt://host.docker.internal:7687"
    neo4j_user = "neo4j"
    neo4j_password = "12345678"
    driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password))
    with driver.session() as session:
        for row in rows:
            start_time = row['window']['start']
            end_time = row['window']['end']
            status = row['status']
            query = """
            MATCH (t:timestamp)
            WHERE t.timestamp >= $start_time AND t.timestamp < $end_time
            SET t.status = $status
            """
            session.run(query, start_time=start_time, end_time=end_time, status=status)

# Write the result to console and also update Neo4j
query = result_df.writeStream \
    .outputMode("update") \
    .foreachBatch(lambda batch_df, batch_id: batch_df.foreach(update_neo4j_status)) \
    .start()

query.awaitTermination()
