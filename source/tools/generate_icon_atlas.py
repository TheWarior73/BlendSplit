#!/usr/bin/env python3
"""Generate BlendSplit's curated icon atlas from Blender 5.2 SVG sources.

Build-only dependencies:
    cairosvg
    pillow

Example:
    python tools/generate_icon_atlas.py \
        --blender-source /path/to/blender/release/datafiles/icons_svg
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from icon_registry import (  # noqa: E402
    ATLAS_COLUMNS,
    ATLAS_FILENAME,
    ATLAS_ROWS,
    ATLAS_TILE_SIZE,
    ICON_IDS,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blender-source", required=True, type=Path)
    parser.add_argument("--blender-license", required=True, type=Path)
    arguments = parser.parse_args()

    try:
        import cairosvg
    except ImportError as error:
        raise SystemExit("Install the build-only dependency cairosvg") from error

    source_dir = arguments.blender_source.resolve()
    output_dir = ROOT / "assets" / "icons"
    vector_dir = output_dir / "source"
    vector_dir.mkdir(parents=True, exist_ok=True)

    atlas = Image.new(
        "RGBA",
        (ATLAS_COLUMNS * ATLAS_TILE_SIZE, ATLAS_ROWS * ATLAS_TILE_SIZE),
        (0, 0, 0, 0),
    )
    for index, identifier in enumerate(ICON_IDS):
        svg_path = source_dir / f"{identifier.lower()}.svg"
        if not svg_path.is_file():
            raise SystemExit(f"Missing Blender SVG: {svg_path}")
        png_bytes = cairosvg.svg2png(
            url=str(svg_path),
            output_width=ATLAS_TILE_SIZE,
            output_height=ATLAS_TILE_SIZE,
        )
        import io

        with Image.open(io.BytesIO(png_bytes)) as tile:
            column = index % ATLAS_COLUMNS
            row = index // ATLAS_COLUMNS
            atlas.alpha_composite(tile.convert("RGBA"), (column * ATLAS_TILE_SIZE, row * ATLAS_TILE_SIZE))
        shutil.copy2(svg_path, vector_dir / svg_path.name)

    atlas.save(output_dir / ATLAS_FILENAME, optimize=True)
    shutil.copy2(arguments.blender_license, output_dir / "GPL3-license.txt")
    print(f"Generated {len(ICON_IDS)} icons in {atlas.width}x{atlas.height} atlas")


if __name__ == "__main__":
    main()
