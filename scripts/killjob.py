from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("KillJobExample").getOrCreate()

# Stop all active streaming queries
for query in spark.streams.active:
    query.stop()

# Stop the Spark session
spark.stop()
