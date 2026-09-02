import time
import threading
from collections import defaultdict, deque
from typing import Dict, Any, List

# Maximum number of raw observations kept per histogram.
# After this limit, old entries are dropped (FIFO).
_HISTOGRAM_MAX_LEN = 1000


class MetricsCollector:
    """Bounded in-memory metrics collector.

    Counters grow proportionally to the number of distinct metric names,
    which is bounded by application code.  Gauges are a single float per
    name.  Histograms are capped at ``_HISTOGRAM_MAX_LEN`` raw
    observations using a :class:`collections.deque` so memory usage
    remains bounded regardless of uptime.
    """

    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._histograms: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=_HISTOGRAM_MAX_LEN)
        )
        self._gauges: Dict[str, float] = {}
        self._lock = threading.Lock()

    def increment(self, name: str, value: int = 1):
        with self._lock:
            self._counters[name] += value

    def observe(self, name: str, value: float):
        with self._lock:
            self._histograms[name].append(value)

    def gauge(self, name: str, value: float):
        with self._lock:
            self._gauges[name] = value

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "histograms": {k: list(v) for k, v in self._histograms.items()},
                "gauges": dict(self._gauges),
            }

    def histogram_stats(self, name: str) -> Dict[str, Any]:
        """Return summary statistics for a named histogram without
        exposing all raw observations."""
        with self._lock:
            values = list(self._histograms.get(name, []))
        if not values:
            return {"name": name, "count": 0}
        values_sorted = sorted(values)
        n = len(values_sorted)
        return {
            "name": name,
            "count": n,
            "min": values_sorted[0],
            "max": values_sorted[-1],
            "mean": sum(values_sorted) / n,
            "p50": values_sorted[n // 2],
            "p95": values_sorted[int(n * 0.95)] if n >= 20 else values_sorted[-1],
            "p99": values_sorted[int(n * 0.99)] if n >= 100 else values_sorted[-1],
        }

    def reset(self):
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._gauges.clear()

# Global singleton
metrics = MetricsCollector()