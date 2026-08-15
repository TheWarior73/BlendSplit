"""Clock implementations used by the run engine."""

from __future__ import annotations

import time
from typing import Protocol


class Clock(Protocol):
    """Small clock interface that makes the run engine deterministic in tests."""

    def now_ns(self) -> int:
        """Return a monotonically increasing timestamp in nanoseconds."""


class PerfCounterClock:
    """Production clock based on Python's monotonic performance counter."""

    def now_ns(self) -> int:
        return time.perf_counter_ns()
