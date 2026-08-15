"""Portable BlendSplit run-list JSON format."""

from __future__ import annotations

from typing import Any, Iterable


FORMAT_ID = "blendsplit.run_list"
FORMAT_VERSION = 1
MAX_SPLITS = 500
MAX_TEXT_LENGTH = 256


class RunListError(ValueError):
    """Raised when an imported run-list file is invalid."""


def create_run_list(title: str, category: str, splits: Iterable[tuple[str, str]]) -> dict[str, Any]:
    """Create a JSON-serializable run-list document."""
    return {
        "format": FORMAT_ID,
        "version": FORMAT_VERSION,
        "run_title": title,
        "category": category,
        "splits": [
            {"name": name, "blender_icon": icon or "NONE"}
            for name, icon in splits
        ],
    }


def parse_run_list(data: Any, valid_icons: set[str] | None = None) -> tuple[str, str, list[tuple[str, str]]]:
    """Validate and normalize a decoded run-list document."""
    if not isinstance(data, dict):
        raise RunListError("The run-list file must contain a JSON object")
    if data.get("format") != FORMAT_ID:
        raise RunListError("This is not a BlendSplit run-list file")
    if data.get("version") != FORMAT_VERSION:
        raise RunListError(f"Unsupported run-list version: {data.get('version')!r}")

    title = _required_text(data.get("run_title"), "run title")
    category = _required_text(data.get("category"), "category")
    raw_splits = data.get("splits")
    if not isinstance(raw_splits, list) or not raw_splits:
        raise RunListError("The run list must contain at least one split")
    if len(raw_splits) > MAX_SPLITS:
        raise RunListError(f"The run list cannot contain more than {MAX_SPLITS} splits")

    splits: list[tuple[str, str]] = []
    for index, raw_split in enumerate(raw_splits, start=1):
        if not isinstance(raw_split, dict):
            raise RunListError(f"Split {index} must be a JSON object")
        name = _required_text(raw_split.get("name"), f"split {index} name")
        icon = raw_split.get("blender_icon", "NONE")
        if not isinstance(icon, str):
            raise RunListError(f"Split {index} icon must be text")
        if valid_icons is not None and icon not in valid_icons:
            icon = "NONE"
        splits.append((name, icon))
    return title, category, splits


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RunListError(f"The {label} cannot be empty")
    text = value.strip()
    if len(text) > MAX_TEXT_LENGTH:
        raise RunListError(f"The {label} cannot exceed {MAX_TEXT_LENGTH} characters")
    return text
