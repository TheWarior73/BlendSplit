from __future__ import annotations

import unittest

from runlist import RunListError, create_run_list, parse_run_list


class RunListTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        document = create_run_list(
            "HATCH Loop",
            "Any%",
            (("Start", "MESH_CUBE"), ("Finish", "NONE")),
        )
        self.assertEqual(
            parse_run_list(document, {"NONE", "MESH_CUBE"}),
            ("HATCH Loop", "Any%", [("Start", "MESH_CUBE"), ("Finish", "NONE")]),
        )

    def test_unknown_icon_falls_back_safely(self) -> None:
        document = create_run_list("Run", "Any%", (("Finish", "FUTURE_ICON"),))
        _title, _category, splits = parse_run_list(document, {"NONE"})
        self.assertEqual(splits, [("Finish", "NONE")])

    def test_rejects_wrong_format_and_empty_splits(self) -> None:
        with self.assertRaises(RunListError):
            parse_run_list({"format": "other", "version": 1, "splits": []})
        with self.assertRaises(RunListError):
            parse_run_list({
                "format": "blendsplit.run_list",
                "version": 1,
                "run_title": "Run",
                "category": "Any%",
                "splits": [],
            })


if __name__ == "__main__":
    unittest.main()
