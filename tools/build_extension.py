#!/usr/bin/env python3
"""Build an installable BlendSplit extension archive."""

from __future__ import annotations

import argparse
from pathlib import Path
import tomllib
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
DIST = ROOT / "dist"
EXCLUDED_DIRS = {"__pycache__", ".git", ".pytest_cache", "dist", "tests"}
EXCLUDED_SUFFIXES = {".pyc", ".zip"}
ARCHIVE_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def included_files() -> list[Path]:
    return sorted(
        path
        for path in SOURCE.rglob("*")
        if path.is_file()
        and not any(part in EXCLUDED_DIRS for part in path.relative_to(SOURCE).parts)
        and path.suffix not in EXCLUDED_SUFFIXES
    )


def build(tag: str | None = None) -> Path:
    manifest_path = SOURCE / "blender_manifest.toml"
    with manifest_path.open("rb") as manifest_file:
        version = tomllib.load(manifest_file)["version"]

    if tag is not None and tag.removeprefix("v") != version:
        raise SystemExit(
            f"Tag {tag!r} does not match blender_manifest.toml version {version!r}"
        )

    DIST.mkdir(exist_ok=True)
    archive_path = DIST / f"blendsplit-{version}.zip"

    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in included_files():
            relative_path = path.relative_to(SOURCE).as_posix()
            info = ZipInfo(relative_path, date_time=ARCHIVE_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())

    return archive_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="Fail if this tag does not match the manifest version")
    args = parser.parse_args()
    print(build(args.tag))


if __name__ == "__main__":
    main()
