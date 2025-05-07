from steam_ui import SteamInterface
from src.steam_client import SteamAPIClient
from pyspark.sql import SparkSession
from src.benchmark_logger import BenchmarkLogger
import time
import os
import shutil

for f in ["benchmarks/benchmark_raw_log.txt", "benchmarks/api_times.log", "benchmarks/spark_times.log", "benchmarks/benchmarks.txt"]:
    try:
        os.remove(f)
    except FileNotFoundError:
        pass
def run_friend_workload_test(steam_id, friend_counts=[10, 25, 50], use_spark=True):
    spark = SparkSession.builder.appName("SteamAnalytics").getOrCreate()
    client = SteamAPIClient()
    ui = SteamInterface(client, spark)
    logger = BenchmarkLogger()

    for count in friend_counts:
        label = f"{'spark' if use_spark else 'manual'}_recommendation_{count}_friends"

        start = time.perf_counter()
        if use_spark:
            ui._benchmark_game_recommendations_spark(steam_id, count, logger)
        else:
            ui._benchmark_game_recommendations_manual(steam_id, count, logger)
        duration = (time.perf_counter() - start) * 1000  # ms
        logger.log_time(label, duration)

    logger.write_summary()

if __name__ == "__main__":
    TEST_STEAM_ID = "76561197979774760"  # Replace with target ID
    run_friend_workload_test(TEST_STEAM_ID, use_spark=True)    # Test PySpark version
    run_friend_workload_test(TEST_STEAM_ID, use_spark=False)   # Test Manual version
