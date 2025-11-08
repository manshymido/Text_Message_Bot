"""Metrics collection for bot operations."""

import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional

from utils.logger import logger


class MetricsCollector:
    """Collects and tracks metrics for the bot."""

    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: Dict[str, float] = defaultdict(float)
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, list] = defaultdict(list)
        self.start_time = time.time()

    def increment(self, metric_name: str, value: int = 1):
        """
        Increment a counter metric.

        Args:
            metric_name: Name of the metric
            value: Value to increment by
        """
        self.counters[metric_name] += value

    def set(self, metric_name: str, value: float):
        """
        Set a gauge metric.

        Args:
            metric_name: Name of the metric
            value: Value to set
        """
        self.metrics[metric_name] = value

    def record_timing(self, metric_name: str, duration: float):
        """
        Record a timing metric.

        Args:
            metric_name: Name of the metric
            duration: Duration in seconds
        """
        self.timers[metric_name].append(duration)
        # Keep only last 1000 timings
        if len(self.timers[metric_name]) > 1000:
            self.timers[metric_name] = self.timers[metric_name][-1000:]

    def time_operation(self, metric_name: str):
        """
        Context manager for timing operations.

        Args:
            metric_name: Name of the metric

        Returns:
            Context manager
        """
        return TimingContext(self, metric_name)

    def get_metrics(self) -> Dict:
        """
        Get all collected metrics.

        Returns:
            Dictionary with all metrics
        """
        # Calculate timing statistics
        timing_stats = {}
        for metric_name, timings in self.timers.items():
            if timings:
                timing_stats[f"{metric_name}_count"] = len(timings)
                timing_stats[f"{metric_name}_avg"] = sum(timings) / len(timings)
                timing_stats[f"{metric_name}_min"] = min(timings)
                timing_stats[f"{metric_name}_max"] = max(timings)
                timing_stats[f"{metric_name}_p95"] = self._percentile(timings, 95)
                timing_stats[f"{metric_name}_p99"] = self._percentile(timings, 99)

        uptime = time.time() - self.start_time

        return {
            "counters": dict(self.counters),
            "gauges": dict(self.metrics),
            "timings": timing_stats,
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _percentile(self, data: list, percentile: float) -> float:
        """Calculate percentile of a list."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def reset(self):
        """Reset all metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.timers.clear()
        self.start_time = time.time()
        logger.info("Metrics reset")

    def get_summary(self) -> str:
        """
        Get a human-readable summary of metrics.

        Returns:
            Summary string
        """
        metrics = self.get_metrics()
        lines = ["📊 Metrics Summary:"]

        if metrics["counters"]:
            lines.append("\n📈 Counters:")
            for name, value in sorted(metrics["counters"].items()):
                lines.append(f"  • {name}: {value}")

        if metrics["gauges"]:
            lines.append("\n📊 Gauges:")
            for name, value in sorted(metrics["gauges"].items()):
                lines.append(f"  • {name}: {value:.2f}")

        if metrics["timings"]:
            lines.append("\n⏱️  Timings:")
            for name, value in sorted(metrics["timings"].items()):
                if "avg" in name:
                    lines.append(f"  • {name}: {value:.3f}s")

        uptime_hours = metrics["uptime_seconds"] / 3600
        lines.append(f"\n⏰ Uptime: {uptime_hours:.2f} hours")

        return "\n".join(lines)


class TimingContext:
    """Context manager for timing operations."""

    def __init__(self, collector: MetricsCollector, metric_name: str):
        """
        Initialize timing context.

        Args:
            collector: MetricsCollector instance
            metric_name: Name of the metric
        """
        self.collector = collector
        self.metric_name = metric_name
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.record_timing(self.metric_name, duration)

