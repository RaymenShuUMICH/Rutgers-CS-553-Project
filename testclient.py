from steam_ui import SteamInterface 
from src.steam_client import SteamAPIClient 
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('SteamAnalytics').getOrCreate()
client = SteamAPIClient()
ui = SteamInterface(client, spark)
ui.main_menu()
