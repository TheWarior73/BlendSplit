from __future__ import annotations

import random
import unittest

from icon_registry import ICON_ID_SET
from random_speedruns import CHALLENGES, choose_random_challenge


class RandomSpeedrunTests(unittest.TestCase):
    def test_library_has_ten_complete_unique_challenges(self) -> None:
        self.assertEqual(len(CHALLENGES), 10)
        self.assertEqual(len({challenge.title for challenge in CHALLENGES}), 10)
        for challenge in CHALLENGES:
            self.assertTrue(challenge.title)
            self.assertTrue(challenge.category)
            self.assertEqual(len(challenge.splits), 5)
            self.assertEqual(len({name for name, _icon in challenge.splits}), 5)
            for name, icon in challenge.splits:
                self.assertTrue(name)
                self.assertIn(icon, ICON_ID_SET)

    def test_randomizer_avoids_immediate_repeat(self) -> None:
        current = CHALLENGES[0].title
        for seed in range(30):
            result = choose_random_challenge(current, random.Random(seed))
            self.assertNotEqual(result.title, current)


if __name__ == "__main__":
    unittest.main()
