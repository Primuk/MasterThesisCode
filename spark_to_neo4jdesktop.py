from pyspark.context import SparkContext
from pyspark.sql.session import SparkSession
neo4j_url = "bolt://host.docker.internal:7687" # put your neo4j url here
neo4j_user = "neo4j"
neo4j_password = "12345678"

spark = SparkSession.builder \
    .appName('Data science workflow with Neo4j and Spark') \
    .config('spark.jars.packages', 'org.neo4j:neo4j-connector-apache-spark_2.13:5.3.0_for_spark_3') \
    .config("neo4j.url", neo4j_url) \
    .config("neo4j.authentication.type", "basic") \
    .config("neo4j.authentication.basic.username", neo4j_user) \
    .config("neo4j.authentication.basic.password", neo4j_password) \
    .getOrCreate()

# Read Parquet files from a directory
parquet_df = spark.read.parquet("./test")

# Show the DataFrame
parquet_df.show()
parquet_df.printSchema()

parquet_df_test=parquet_df.select("sensor","temperature")
parquet_df_test.printSchema()
#test neo4j connection
parquet_df_test.write\
 .format('org.neo4j.spark.DataSource')\
 .mode('append')\
 .option('labels', ':sensor')\
 .save()