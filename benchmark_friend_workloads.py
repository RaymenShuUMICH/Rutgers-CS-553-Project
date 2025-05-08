from steam_ui import SteamInterface
from src.steam_client import SteamAPIClient
from pyspark.sql import SparkSession
from src.benchmark_logger import BenchmarkLogger
from rich.prompt import Prompt
import time
import os
import shutil

for f in ["benchmarks/benchmark_raw_log.txt", "benchmarks/api_times.log", "benchmarks/spark_times.log", "benchmarks/benchmarks.txt", "benchmarks/resource_usage.log"]:
    try:
        os.remove(f)
    except FileNotFoundError:
        pass
def run_friend_workload_test(steam_id, friend_counts=[10, 25, 50], use_spark=True, useCache = True):
    spark = SparkSession.builder.appName("SteamAnalytics").getOrCreate()
    client = SteamAPIClient()
    ui = SteamInterface(client, spark)
    logger = BenchmarkLogger()

    for count in friend_counts:
        label = f"{'spark' if use_spark else 'manual'}_recommendation_{count}_friends"

        if useCache:
            label = label + "_useCache"
        else:
            label = label + "_noCache"

        logger.start_monitoring(label)
        start = time.perf_counter()
        if use_spark:
            ui._benchmark_game_recommendations_spark(steam_id, count, logger, useCache)
        else:
            ui._benchmark_game_recommendations_manual(steam_id, count, logger, useCache)
        duration = (time.perf_counter() - start) * 1000  # ms

        logger.stop_monitoring()
        logger.log_time(label, duration)
        

    logger.write_summary()

if __name__ == "__main__":
    #TEST_STEAM_ID = "76561198268731868"  # Replace with target ID
    TEST_STEAM_ID = Prompt.ask("Enter target ID: ", default = "76561197979774760")
    run_friend_workload_test(TEST_STEAM_ID, use_spark=True)    # Test PySpark version
    run_friend_workload_test(TEST_STEAM_ID, use_spark=False)   # Test Manual version

    run_friend_workload_test(TEST_STEAM_ID, use_spark=True, useCache=False)    # Test PySpark version, no cache
    run_friend_workload_test(TEST_STEAM_ID, use_spark=False, useCache=False)   # Test Manual version, no cache
    
