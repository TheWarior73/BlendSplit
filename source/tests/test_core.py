from __future__ import annotations

import unittest

from core.formatting import format_delta, format_time
from core.run_engine import RunEngine, RunState


class FakeClock:
    def __init__(self) -> None:
        self.value = 0

    def now_ns(self) -> int:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += round(seconds * 1_000_000_000)


class RunEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.engine = RunEngine(self.clock)

    def test_full_run(self) -> None:
        self.engine.start(2)
        self.clock.advance(1.25)
        first = self.engine.split()
        self.clock.advance(2.5)
        second = self.engine.split()

        self.assertEqual(first.cumulative_ns, 1_250_000_000)
        self.assertEqual(first.segment_ns, 1_250_000_000)
        self.assertEqual(second.segment_ns, 2_500_000_000)
        self.assertEqual(self.engine.state, RunState.FINISHED)
        self.assertEqual(self.engine.elapsed_ns(), 3_750_000_000)

    def test_pause_is_excluded(self) -> None:
        self.engine.start(1)
        self.clock.advance(1)
        self.assertTrue(self.engine.pause())
        self.clock.advance(10)
        self.assertEqual(self.engine.elapsed_ns(), 1_000_000_000)
        self.assertTrue(self.engine.resume())
        self.clock.advance(2)
        self.assertEqual(self.engine.split().cumulative_ns, 3_000_000_000)

    def test_skip_and_undo(self) -> None:
        self.engine.start(3)
        self.clock.advance(1)
        skipped = self.engine.skip()
        self.clock.advance(1)
        combined = self.engine.split()
        self.assertTrue(skipped.skipped)
        self.assertIsNone(combined.segment_ns)
        self.engine.undo()
        self.assertEqual(self.engine.current_index, 1)
        self.assertEqual(self.engine.state, RunState.RUNNING)

    def test_undo_finished_run(self) -> None:
        self.engine.start(1)
        self.clock.advance(1)
        self.engine.split()
        self.assertEqual(self.engine.state, RunState.FINISHED)
        self.engine.undo()
        self.assertEqual(self.engine.state, RunState.RUNNING)
        self.assertEqual(self.engine.current_index, 0)

    def test_reset(self) -> None:
        self.engine.start(2)
        self.clock.advance(1)
        self.engine.split()
        self.engine.reset()
        self.assertEqual(self.engine.state, RunState.IDLE)
        self.assertEqual(self.engine.elapsed_ns(), 0)
        self.assertEqual(self.engine.results, [])


class FormattingTests(unittest.TestCase):
    def test_time_formats(self) -> None:
        self.assertEqual(format_time(None), "—")
        self.assertEqual(format_time(3_456_000_000, 2), "00:03.46")
        self.assertEqual(format_time(63_456_000_000, 2), "01:03.46")
        self.assertEqual(format_time(3_723_456_000_000, 2), "1:02:03.46")
        self.assertEqual(format_time(59_999_000_000, 2), "01:00.00")

    def test_delta_formats(self) -> None:
        self.assertEqual(format_delta(-740_000_000, 2), "−.74")
        self.assertEqual(format_delta(1_250_000_000, 2), "+1.25")



if __name__ == "__main__":
    unittest.main()
