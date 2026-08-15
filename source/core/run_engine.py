"""Pure timing state machine for BlendSplit."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .clock import Clock, PerfCounterClock


class RunState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


@dataclass(frozen=True, slots=True)
class SplitResult:
    """One completed or skipped segment."""

    index: int
    cumulative_ns: int | None
    segment_ns: int | None
    skipped: bool = False


class RunEngine:
    """Accurate, UI-independent speedrun timer.

    Time is sampled only when requested. UI refreshes never contribute to the
    measured duration, so viewport lag cannot make the timer run slowly.
    """

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or PerfCounterClock()
        self.state = RunState.IDLE
        self.segment_count = 0
        self.started_at_ns = 0
        self.paused_at_ns: int | None = None
        self.paused_total_ns = 0
        self.finished_elapsed_ns: int | None = None
        self.results: list[SplitResult] = []

    @property
    def current_index(self) -> int:
        return len(self.results)

    @property
    def is_active(self) -> bool:
        return self.state in {RunState.RUNNING, RunState.PAUSED}

    def elapsed_ns(self, now_ns: int | None = None) -> int:
        if self.state == RunState.IDLE:
            return 0
        if self.state == RunState.FINISHED:
            return self.finished_elapsed_ns or 0

        sampled_ns = (
            self.paused_at_ns
            if self.state == RunState.PAUSED
            else (now_ns if now_ns is not None else self._clock.now_ns())
        )
        assert sampled_ns is not None
        return max(0, sampled_ns - self.started_at_ns - self.paused_total_ns)

    def start(self, segment_count: int) -> None:
        if segment_count < 1:
            raise ValueError("A run needs at least one split")
        self.segment_count = segment_count
        self.started_at_ns = self._clock.now_ns()
        self.paused_at_ns = None
        self.paused_total_ns = 0
        self.finished_elapsed_ns = None
        self.results.clear()
        self.state = RunState.RUNNING

    def pause(self) -> bool:
        if self.state != RunState.RUNNING:
            return False
        self.paused_at_ns = self._clock.now_ns()
        self.state = RunState.PAUSED
        return True

    def resume(self) -> bool:
        if self.state != RunState.PAUSED or self.paused_at_ns is None:
            return False
        self.paused_total_ns += self._clock.now_ns() - self.paused_at_ns
        self.paused_at_ns = None
        self.state = RunState.RUNNING
        return True

    def toggle_pause(self) -> bool:
        return self.resume() if self.state == RunState.PAUSED else self.pause()

    def split(self) -> SplitResult:
        if self.state != RunState.RUNNING:
            raise RuntimeError("The run is not running")
        if self.current_index >= self.segment_count:
            raise RuntimeError("Every segment is already complete")

        cumulative_ns = self.elapsed_ns()
        previous_ns = self._previous_recorded_cumulative()
        # A segment following a skip spans multiple named splits and is not a
        # valid individual best segment.
        segment_ns = (
            cumulative_ns - previous_ns
            if previous_ns is not None and (not self.results or not self.results[-1].skipped)
            else None
        )
        result = SplitResult(self.current_index, cumulative_ns, segment_ns)
        self.results.append(result)

        if self.current_index == self.segment_count:
            self.finished_elapsed_ns = cumulative_ns
            self.state = RunState.FINISHED
        return result

    def skip(self) -> SplitResult:
        if self.state != RunState.RUNNING:
            raise RuntimeError("The run is not running")
        if self.current_index >= self.segment_count - 1:
            raise RuntimeError("The final split cannot be skipped")
        result = SplitResult(self.current_index, None, None, skipped=True)
        self.results.append(result)
        return result

    def undo(self) -> SplitResult:
        if not self.results:
            raise RuntimeError("There is no split to undo")
        if self.state not in {RunState.RUNNING, RunState.PAUSED, RunState.FINISHED}:
            raise RuntimeError("The run is not active")
        result = self.results.pop()
        if self.state == RunState.FINISHED:
            self.finished_elapsed_ns = None
            self.state = RunState.RUNNING
        return result

    def reset(self) -> None:
        self.state = RunState.IDLE
        self.segment_count = 0
        self.started_at_ns = 0
        self.paused_at_ns = None
        self.paused_total_ns = 0
        self.finished_elapsed_ns = None
        self.results.clear()

    def _previous_recorded_cumulative(self) -> int | None:
        for result in reversed(self.results):
            if result.cumulative_ns is not None:
                return result.cumulative_ns
        return 0
