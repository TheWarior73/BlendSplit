from __future__ import annotations

import pathlib
import unittest

from PIL import Image

from icon_registry import (
    ATLAS_COLUMNS,
    ATLAS_FILENAME,
    ATLAS_ROWS,
    ATLAS_TILE_SIZE,
    ICON_IDS,
    ICON_ID_SET,
    icon_uv,
    normalize_icon,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]


class IconRegistryTests(unittest.TestCase):
    def test_curated_registry_is_complete_and_unique(self) -> None:
        self.assertEqual(len(ICON_IDS), 100)
        self.assertEqual(len(ICON_ID_SET), 100)
        for identifier in ICON_IDS:
            self.assertRegex(identifier, r"^[A-Z][A-Z0-9_]+$")
            self.assertTrue((ROOT / "assets" / "icons" / "source" / f"{identifier.lower()}.svg").is_file())

    def test_uvs_are_unique_and_inside_texture(self) -> None:
        bounds = [icon_uv(identifier) for identifier in ICON_IDS]
        self.assertEqual(len(set(bounds)), len(ICON_IDS))
        for uv in bounds:
            assert uv is not None
            u_min, v_min, u_max, v_max = uv
            self.assertTrue(0.0 <= u_min < u_max <= 1.0)
            self.assertTrue(0.0 <= v_min < v_max <= 1.0)
        self.assertIsNone(icon_uv("NONE"))

    def test_atlas_dimensions_and_licensing_assets(self) -> None:
        atlas_path = ROOT / "assets" / "icons" / ATLAS_FILENAME
        with Image.open(atlas_path) as atlas:
            self.assertEqual(atlas.mode, "RGBA")
            self.assertEqual(
                atlas.size,
                (ATLAS_COLUMNS * ATLAS_TILE_SIZE, ATLAS_ROWS * ATLAS_TILE_SIZE),
            )
            alpha = atlas.getchannel("A")
            for index, identifier in enumerate(ICON_IDS):
                column = index % ATLAS_COLUMNS
                row = index // ATLAS_COLUMNS
                tile = alpha.crop((
                    column * ATLAS_TILE_SIZE,
                    row * ATLAS_TILE_SIZE,
                    (column + 1) * ATLAS_TILE_SIZE,
                    (row + 1) * ATLAS_TILE_SIZE,
                ))
                self.assertIsNotNone(tile.getbbox(), f"Atlas tile is empty: {identifier}")
        self.assertTrue((ROOT / "assets" / "icons" / "NOTICE.md").is_file())
        self.assertTrue((ROOT / "assets" / "icons" / "GPL3-license.txt").is_file())

    def test_unknown_icons_normalize_to_none(self) -> None:
        self.assertEqual(normalize_icon("MESH_CUBE"), "MESH_CUBE")
        self.assertEqual(normalize_icon("EVENT_F12"), "NONE")
        self.assertEqual(normalize_icon(None), "NONE")


if __name__ == "__main__":
    unittest.main()
