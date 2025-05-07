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

            # Comparative summary
            out.write("\n=== Comparison Table (Manual vs Spark with/without cache) ===\n")
            header = f"{'Friends':<10}{'Manual (Cached)':<18}{'Manual (No Cache)':<20}{'Spark (Cached)':<18}{'Spark (No Cache)'}\n"
            out.write(header)
            out.write(f"{'-'*len(header)}\n")

            friend_counts = set()
            for label in label_times:
                parts = label.split("_")
                if len(parts) >= 4 and parts[2].isdigit():
                    friend_counts.add(int(parts[2]))

            for count in sorted(friend_counts):
                def get_avg(label_prefix):
                    times = label_times.get(label_prefix, [])
                    return sum(times) / len(times) if times else 0.0

                manual_cache = get_avg(f"manual_recommendation_{count}_friends_useCache")
                manual_nocache = get_avg(f"manual_recommendation_{count}_friends_noCache")
                spark_cache = get_avg(f"spark_recommendation_{count}_friends_useCache")
                spark_nocache = get_avg(f"spark_recommendation_{count}_friends_noCache")

                out.write(f"{count:<10}{manual_cache:<18.3f}{manual_nocache:<20.3f}{spark_cache:<18.3f}{spark_nocache:.3f}\n")


    @contextmanager
    def timed(self, label):
        start = time.perf_counter()
        yield
        duration = (time.perf_counter() - start) * 1000  # ms
        self.log_time(label, duration)
