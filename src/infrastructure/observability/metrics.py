from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Counter:
    name: str
    value: int = 0

    def increment(self, amount: int = 1) -> None:
        self.value += amount


@dataclass
class Gauge:
    name: str
    value: float = 0.0

    def set(self, value: float) -> None:
        self.value = value


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._lock = threading.Lock()

    def counter(self, name: str) -> Counter:
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name=name)
            return self._counters[name]

    def gauge(self, name: str) -> Gauge:
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name=name)
            return self._gauges[name]

    def snapshot(self) -> dict[str, Any]:
        return {
            "counters": {k: v.value for k, v in self._counters.items()},
            "gauges": {k: v.value for k, v in self._gauges.items()},
        }


_metrics = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    return _metrics
