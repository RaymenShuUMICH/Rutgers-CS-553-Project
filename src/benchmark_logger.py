# src/benchmark_logger.py
import os
import time
import psutil
import threading
from pathlib import Path
from contextlib import contextmanager


class BenchmarkLogger:
    def __init__(self, base_dir="benchmarks"):
        self.base_dir = Path(base_dir)
        self.api_log = self.base_dir / "api_times.log"
        self.spark_log = self.base_dir / "spark_times.log"
        self.summary_log = self.base_dir / "benchmarks.txt"
        self.resource_log = self.base_dir / "resource_usage.log"
        self.base_dir.mkdir(exist_ok=True)
        self._monitoring = False

    def log_time(self, label, duration_ms):
        with open(self.spark_log, "a") as f:  # use a single combined log
            f.write(f"{label}: {duration_ms:.3f}\n")

    def _monitor(self, label, interval=0.1):
        process = psutil.Process(os.getpid())
        samples = []

        while self._monitoring:
            cpu = process.cpu_percent(interval=None)
            mem = process.memory_info().rss / (1024 * 1024)
            samples.append((cpu, mem))
            time.sleep(interval)

        if samples:
            avg_cpu = sum(cpu for cpu, _ in samples) / len(samples)
            avg_mem = sum(mem for _, mem in samples) / len(samples)
            with open(self.base_dir / "resource_usage.log", "a") as f:
                f.write(f"{label}: AVG_CPU={avg_cpu:.2f}% AVG_MEM={avg_mem:.2f}MB over {len(samples)} samples\n")

    def start_monitoring(self, label):
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor, args=(label,))
        self._monitor_thread.start()

    def stop_monitoring(self):
        self._monitoring = False
        self._monitor_thread.join()

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
