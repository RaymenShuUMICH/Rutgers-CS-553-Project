from pyspark.sql.functions import from_unixtime, avg, max
from config.settings import BASE_DIR 
from pyspark.sql import SparkSession
from pyspark.sql import Row
from pyspark.sql.functions import col, explode, sum as _sum
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas

def recommend_top_games(spark, all_games, user_owned_appids=None):
    """
    Given a list of (appid, name, playtime), return top 10 recommended games
    excluding any games in `user_owned_appids`.
    """
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

def find_most_played(spark, steam_id):
    """Find single most played game"""
    path = str(BASE_DIR / f"data/raw/games/games_{steam_id}.json")
    games_df = spark.read.json(path)
    
    result = games_df.select(
        explode(col("response.games")).alias("game")
    ).select(
        col("game.name").alias("game"),
        col("game.playtime_forever").cast("integer").alias("minutes")
    ).orderBy(col("minutes").desc()).first()
    
    return (result["game"], result["minutes"])
def generate_full_report(spark, steam_id):
    """Generate PDF with charts and stats"""
    # Load data
    games_df = spark.read.json(f"data/raw/games/games_{steam_id}.json")
    
    # Transform data
    games = games_df.select(
        explode(col("response.games")).alias("game")
    ).select(
        col("game.name"),
        col("game.playtime_forever")
    ).toPandas()

    # Generate visualization
    plt.figure(figsize=(10,6))
    games.nlargest(10, 'playtime_forever').plot.barh(
        x='name', 
        y='playtime_forever',
        title='Top 10 Played Games'
    )
    plt.savefig('temp_chart.png')

    # Create PDF
    c = canvas.Canvas(f"reports/{steam_id}_report.pdf")
    c.drawString(100, 800, f"Steam Gaming Report for {steam_id}")
    c.drawImage('temp_chart.png', 50, 400, width=500, height=300)
    c.save()
    # spark_processor.py
    def calculate_play_patterns(spark, steam_id):
        """Analyze playtime distribution across days/hours"""
        df = spark.read.json(f"data/raw/games/games_{steam_id}.json")
        return df.select(
            explode(col("response.games")).alias("game")
        ).select(
            col("game.name"),
            col("game.playtime_2weeks"),
            col("game.playtime_forever")
        ).withColumn("recent_ratio", col("playtime_2weeks")/col("playtime_forever"))

    # spark_processor.py
def analyze_play_habits(spark, steam_id, days_back=30):
    path = str(BASE_DIR / f"data/raw/games/games_{steam_id}.json")
    df = spark.read.json(path)
    
    return df.select(
        explode(col("response.games")).alias("game")
    ).select(
        col("game.name"),
        col("game.playtime_2weeks"),
        col("game.playtime_forever")
    ).groupBy("name").agg(
        _sum("playtime_forever").alias("total_playtime"),
        avg("playtime_2weeks").alias("recent_avg")
    ).toPandas()
