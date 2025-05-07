# src/benchmark_logger.py
import os
import time
from pathlib import Path
from contextlib import contextmanager

class BenchmarkLogger:
    def __init__(self, base_dir="benchmarks"):
        self.base_dir = Path(base_dir)
        self.api_log = self.base_dir / "api_times.log"
        self.spark_log = self.base_dir / "spark_times.log"
        self.summary_log = self.base_dir / "benchmarks.txt"
        self.base_dir.mkdir(exist_ok=True)

    def log_time(self, label, duration_ms):
        with open(self.spark_log, "a") as f:  # use a single combined log
            f.write(f"{label}: {duration_ms:.3f}\n")


    def write_summary(self):
        label_times = {}

        try:
            with open(self.spark_log) as f:
                for line in f:
                    if ':' not in line:
                        continue
                    label, value = line.strip().split(":")
                    label = label.strip()
                    value = float(value.strip())

                    if label not in label_times:
                        label_times[label] = []
                    label_times[label].append(value)
        except FileNotFoundError:
            return

        with open(self.summary_log, "w") as out:
            out.write("=== Individual Averages ===\n")
            for label in sorted(label_times):
                times = label_times[label]
                avg_time = sum(times) / len(times)
                out.write(f"{label}: {avg_time:.3f} ms (avg over {len(times)} runs)\n")

            # Build comparative summary
            out.write("\n=== Comparison Table (Manual vs Spark) ===\n")
            out.write(f"{'Friends':<10}{'Manual Avg (ms)':<20}{'Spark Avg (ms)'}\n")
            out.write(f"{'-'*50}\n")

            friend_counts = set()
            for label in label_times:
                if label.startswith("manual"):
                    friend_counts.add(int(label.split("_")[2]))

            for count in sorted(friend_counts):
                manual_label = f"manual_recommendation_{count}_friends"
                spark_label = f"spark_recommendation_{count}_friends"
                manual_avg = sum(label_times.get(manual_label, [0])) / max(len(label_times.get(manual_label, [])), 1)
                spark_avg = sum(label_times.get(spark_label, [0])) / max(len(label_times.get(spark_label, [])), 1)
                out.write(f"{count:<10}{manual_avg:<20.3f}{spark_avg:.3f}\n")



    @contextmanager
    def timed(self, label):
        start = time.perf_counter()
        yield
        duration = (time.perf_counter() - start) * 1000  # ms
        self.log_time(label, duration)
