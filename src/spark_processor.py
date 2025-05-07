from pyspark.sql.functions import from_unixtime, avg, max
from config.settings import BASE_DIR 
from pyspark.sql import SparkSession
from pyspark.sql import Row
from pyspark.sql.functions import col, explode, sum as _sum
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from src.benchmark_logger import BenchmarkLogger


logger = BenchmarkLogger()
def recommend_top_games(spark, all_games, user_owned_appids=None):
    """
    Given a list of (appid, name, playtime), return top 10 recommended games
    excluding any games in `user_owned_appids`.
    """
    with logger.timed("spark"):
        if user_owned_appids is None:
            user_owned_appids = set()

        rows = [
            Row(appid=appid, name=name, playtime=playtime)
            for appid, name, playtime in all_games
            if appid not in user_owned_appids
        ]
        
        if not rows:
            return spark.createDataFrame([], schema="appid INT, name STRING, total_playtime DOUBLE").toPandas()

        df = spark.createDataFrame(rows)

        result = df.groupBy("appid", "name") \
                .agg(_sum("playtime").alias("total_playtime")) \
                .orderBy("total_playtime", ascending=False) \
                .limit(10)

        return result.toPandas()
