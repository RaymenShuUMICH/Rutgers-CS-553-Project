from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, sum as _sum
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas

def find_most_played(spark, steam_id):
    """Find single most played game"""
    games_df = spark.read.json(f"data/raw/games/games_{steam_id}.json")
    
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