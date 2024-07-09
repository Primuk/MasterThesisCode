from pyspark.sql import SparkSession
from pyspark.sql.functions import window, min, max, col, avg, count
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# Initialize SparkSession
spark = SparkSession.builder \
    .appName("Streaming Aggregation and Neo4j Update") \
    .getOrCreate()

neo4j_url = "bolt://host.docker.internal:7687"
neo4j_user = "neo4j"
neo4j_password = "12345678"

# Define the schema for reading data from HDFS
schema_read = StructType([
    StructField("joint_name", StringType(), True),
    StructField("timestamp", TimestampType(), True),
    StructField("velocity", DoubleType(), True),
    StructField("current", DoubleType(), True),
    StructField("position_x", DoubleType(), True),
    StructField("position_y", DoubleType(), True),
    StructField("position_z", DoubleType(), True),
    StructField("force_x", DoubleType(), True),
    StructField("force_y", DoubleType(), True),
    StructField("force_z", DoubleType(), True),
    StructField("torque_x", DoubleType(), True),
    StructField("torque_y", DoubleType(), True),
    StructField("torque_z", DoubleType(), True),
    StructField("environment_temperature", DoubleType(), True),
    StructField("environment_humidity", StringType(), True),
    StructField("environment_air_quality", StringType(), True),
    StructField("log_type", StringType(), True),
    StructField("log_timestamp", TimestampType(), True),
    StructField("log_message", StringType(), True)
])

# Read streaming data from HDFS
streaming_df = spark.readStream \
    .schema(schema_read) \
    .format("parquet") \
    .load("/app/update/staging")

# Calculate min, max, and average temperatures over a 5-minute window
result_df_log = streaming_df \
    .withWatermark("timestamp", "5 minutes") \
    .groupBy(window("timestamp", "5 minutes"), "log_type") \
    .agg(
        count("log_type").alias("log_count")
    )
result_df_log = result_df_log.select(
    col("window.start").alias("window_start"),
    col("window.end").alias("window_end"),
    col("log_type").alias("log_type"),
    col("log_count")
)

result_df_log.printSchema()
streaming_df = streaming_df.withColumn("environment_humidity", col("environment_humidity").cast(DoubleType()))
result_df_env = streaming_df \
    .withWatermark("timestamp", "5 minutes") \
    .groupBy(window("timestamp", "5 minutes")) \
    .agg(
        avg("environment_humidity").alias("avg_humidity")
    )
result_df_env = result_df_env.select(
    col("window.start").alias("window_start"),
    col("window.end").alias("window_end"),
    col("avg_humidity").alias("avg_humidity"),
)

write_query1 = '''
MATCH (log:Log {name: 'Log'})
MERGE (log)-[r:HAS_LOG_SUMMARY {logType: event.log_type}]->(logSummary:LogSummary {logType: event.log_type})
SET logSummary.count = event.log_count, logSummary.timestamp = event.window_start
'''

write_query2 = '''
MATCH (environment:Environment {name: 'Environment'})
MERGE (environment)-[:HAS_ENV_SUMMARY {type: 'Humidity'} ]->(environmentSummary:EnvironmentSummary)
SET environmentSummary.avg_humidity = event.avg_humidity, environmentSummary.timestamp = event.window_start
'''
query = result_df_log.writeStream \
    .format("org.neo4j.spark.DataSource") \
    .option("url", neo4j_url) \
    .option("authentication.basic.username", neo4j_user) \
    .option("authentication.basic.password", neo4j_password) \
    .option("query", write_query1) \
    .option("save.mode", "Overwrite") \
    .option("checkpointLocation", "/app/update/aggregatorUpdates") \
    .start()

query = result_df_env.writeStream \
    .format("org.neo4j.spark.DataSource") \
    .option("url", neo4j_url) \
    .option("authentication.basic.username", neo4j_user) \
    .option("authentication.basic.password", neo4j_password) \
    .option("query", write_query2) \
    .option("save.mode", "Overwrite") \
    .option("checkpointLocation", "/app/update/envUpdates") \
    .start()

query.awaitTermination()
query.awaitTermination()