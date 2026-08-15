from __future__ import annotations

import json
import pathlib
import tempfile
import unittest

from profile_store import (
    DEFAULT_UI_SETTINGS,
    backup_path,
    empty_library,
    load_library,
    normalize_library,
    save_library,
)


ICONS = {"NONE", "MESH_CUBE"}


def sample_library(title: str = "Cube Run") -> dict:
    return {
        "schema_version": 1,
        "active_profile_id": "cube",
        "profiles": {
            "cube": {
                "id": "cube",
                "revision": 1,
                "title": title,
                "category": "Any%",
                "attempts": 4,
                "splits": [{
                    "name": "Cube",
                    "blender_icon": "MESH_CUBE",
                    "pb_time": 4.2,
                    "best_segment": 4.0,
                }],
            },
        },
    }


class ProfileStoreTests(unittest.TestCase):
    def test_atomic_round_trip_and_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "profiles.json"
            save_library(path, sample_library(), ICONS)
            self.assertEqual(load_library(path, ICONS)["profiles"]["cube"]["attempts"], 4)
            save_library(path, sample_library("Updated Run"), ICONS)
            self.assertTrue(backup_path(path).is_file())
            self.assertEqual(load_library(path, ICONS)["profiles"]["cube"]["title"], "Updated Run")

    def test_corrupt_primary_uses_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "profiles.json"
            save_library(path, sample_library(), ICONS)
            save_library(path, sample_library("New"), ICONS)
            path.write_text("not json", encoding="utf-8")
            self.assertEqual(load_library(path, ICONS)["profiles"]["cube"]["title"], "Cube Run")

    def test_unknown_icons_normalize_and_missing_store_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "profiles.json"
            self.assertEqual(load_library(path, ICONS), empty_library())
            data = sample_library()
            data["profiles"]["cube"]["splits"][0]["blender_icon"] = "FUTURE_ICON"
            save_library(path, data, ICONS)
            icon = load_library(path, ICONS)["profiles"]["cube"]["splits"][0]["blender_icon"]
            self.assertEqual(icon, "NONE")

    def test_pre_12_library_gets_safe_ui_defaults(self) -> None:
        normalized = normalize_library(sample_library(), ICONS)
        self.assertEqual(normalized["ui_settings"], DEFAULT_UI_SETTINGS)
        self.assertFalse(normalized["ui_settings_initialized"])

    def test_ui_settings_normalize_and_clamp(self) -> None:
        data = sample_library()
        data["ui_settings_initialized"] = True
        data["ui_settings"] = {
            "show_overlay": False,
            "show_attempts": False,
            "show_pb": "not a boolean",
            "overlay_anchor": "BOTTOM_RIGHT",
            "overlay_offset_x": 3000,
            "overlay_offset_y": -4,
            "overlay_scale": 9.0,
            "overlay_width": 100,
            "background_opacity": float("nan"),
            "visible_splits": 99,
            "decimals": "3",
        }
        normalized = normalize_library(data, ICONS)
        ui = normalized["ui_settings"]
        self.assertTrue(normalized["ui_settings_initialized"])
        self.assertFalse(ui["show_overlay"])
        self.assertFalse(ui["show_attempts"])
        self.assertTrue(ui["show_pb"])
        self.assertEqual(ui["overlay_anchor"], "BOTTOM_RIGHT")
        self.assertEqual(ui["overlay_offset_x"], 2000)
        self.assertEqual(ui["overlay_offset_y"], 0)
        self.assertEqual(ui["overlay_scale"], 2.5)
        self.assertEqual(ui["overlay_width"], 220)
        self.assertEqual(ui["background_opacity"], 0.92)
        self.assertEqual(ui["visible_splits"], 20)
        self.assertEqual(ui["decimals"], "3")


if __name__ == "__main__":
    unittest.main()
