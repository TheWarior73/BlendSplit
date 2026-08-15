"""Versioned, dependency-free persistence for BlendSplit profiles."""

from __future__ import annotations

import json
import math
import os
import shutil
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
MAX_PROFILES = 250
MAX_SPLITS = 500
MAX_TEXT_LENGTH = 256

DEFAULT_UI_SETTINGS: dict[str, Any] = {
    "show_overlay": True,
    "show_attempts": True,
    "show_pb": True,
    "overlay_anchor": "TOP_LEFT",
    "overlay_offset_x": 18,
    "overlay_offset_y": 100,
    "overlay_scale": 1.0,
    "overlay_width": 285,
    "background_opacity": 0.92,
    "visible_splits": 8,
    "decimals": "2",
}


class ProfileStoreError(ValueError):
    """Raised when a profile library cannot be validated or saved."""


def empty_library() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "active_profile_id": "",
        "profiles": {},
        "ui_settings": DEFAULT_UI_SETTINGS.copy(),
        "ui_settings_initialized": False,
    }


def load_library(path: Path, valid_icons: set[str] | frozenset[str]) -> dict[str, Any]:
    """Load a library, falling back to its backup and then an empty library."""
    for candidate in (path, backup_path(path)):
        try:
            with candidate.open("r", encoding="utf-8") as handle:
                return normalize_library(json.load(handle), valid_icons)
        except (OSError, UnicodeError, json.JSONDecodeError, ProfileStoreError):
            continue
    return empty_library()


def save_library(path: Path, library: dict[str, Any], valid_icons: set[str] | frozenset[str]) -> None:
    """Atomically save a validated library while preserving one valid backup."""
    normalized = normalize_library(library, valid_icons)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    backup = backup_path(path)
    backup_temporary = backup.with_name(backup.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(normalized, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        # Do not replace a good backup with a corrupt primary file.
        if path.is_file():
            try:
                with path.open("r", encoding="utf-8") as handle:
                    normalize_library(json.load(handle), valid_icons)
                shutil.copyfile(path, backup_temporary)
                os.replace(backup_temporary, backup)
            except (OSError, UnicodeError, json.JSONDecodeError, ProfileStoreError):
                backup_temporary.unlink(missing_ok=True)
        os.replace(temporary, path)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        backup_temporary.unlink(missing_ok=True)
        raise ProfileStoreError(f"Could not save profiles: {error}") from error


def backup_path(path: Path) -> Path:
    return path.with_name(path.name + ".backup")


def normalize_library(data: Any, valid_icons: set[str] | frozenset[str]) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ProfileStoreError("Unsupported profile-library format")
    raw_profiles = data.get("profiles")
    if not isinstance(raw_profiles, dict) or len(raw_profiles) > MAX_PROFILES:
        raise ProfileStoreError("Invalid profile collection")

    profiles: dict[str, Any] = {}
    for profile_id, profile in raw_profiles.items():
        if not isinstance(profile_id, str) or not profile_id or len(profile_id) > 64:
            raise ProfileStoreError("Invalid profile identifier")
        profiles[profile_id] = normalize_profile(profile, profile_id, valid_icons)

    active = data.get("active_profile_id", "")
    if not isinstance(active, str) or active not in profiles:
        active = ""
    return {
        "schema_version": SCHEMA_VERSION,
        "active_profile_id": active,
        "profiles": profiles,
        "ui_settings": normalize_ui_settings(data.get("ui_settings")),
        "ui_settings_initialized": data.get("ui_settings_initialized") is True,
    }


def normalize_ui_settings(data: Any) -> dict[str, Any]:
    """Normalize global overlay settings, accepting pre-1.2 libraries."""
    raw = data if isinstance(data, dict) else {}
    result = DEFAULT_UI_SETTINGS.copy()
    for name in ("show_overlay", "show_attempts", "show_pb"):
        if isinstance(raw.get(name), bool):
            result[name] = raw[name]

    anchor = raw.get("overlay_anchor")
    if anchor in {"TOP_LEFT", "TOP_RIGHT", "BOTTOM_LEFT", "BOTTOM_RIGHT"}:
        result["overlay_anchor"] = anchor
    decimals = raw.get("decimals")
    if decimals in {"1", "2", "3"}:
        result["decimals"] = decimals

    result["overlay_offset_x"] = _clamped_int(raw.get("overlay_offset_x"), 0, 2000, 18)
    result["overlay_offset_y"] = _clamped_int(raw.get("overlay_offset_y"), 0, 2000, 100)
    result["overlay_width"] = _clamped_int(raw.get("overlay_width"), 220, 420, 285)
    result["visible_splits"] = _clamped_int(raw.get("visible_splits"), 3, 20, 8)
    result["overlay_scale"] = _clamped_float(raw.get("overlay_scale"), 0.6, 2.5, 1.0)
    result["background_opacity"] = _clamped_float(raw.get("background_opacity"), 0.15, 1.0, 0.92)
    return result


def normalize_profile(
    data: Any,
    profile_id: str,
    valid_icons: set[str] | frozenset[str],
) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ProfileStoreError("Invalid profile")
    title = _text(data.get("title"), "profile title")
    category = _text(data.get("category"), "profile category")
    attempts = data.get("attempts", 0)
    revision = data.get("revision", 1)
    if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 0:
        raise ProfileStoreError("Invalid attempt count")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ProfileStoreError("Invalid profile revision")

    raw_splits = data.get("splits")
    if not isinstance(raw_splits, list) or len(raw_splits) > MAX_SPLITS:
        raise ProfileStoreError("Invalid profile splits")
    splits = []
    for raw_split in raw_splits:
        if not isinstance(raw_split, dict):
            raise ProfileStoreError("Invalid profile split")
        icon = raw_split.get("blender_icon", "NONE")
        if not isinstance(icon, str) or icon not in valid_icons:
            icon = "NONE"
        splits.append({
            "name": _text(raw_split.get("name"), "split name"),
            "blender_icon": icon,
            "pb_time": _time(raw_split.get("pb_time", -1.0)),
            "best_segment": _time(raw_split.get("best_segment", -1.0)),
        })
    return {
        "id": profile_id,
        "revision": revision,
        "title": title,
        "category": category,
        "attempts": attempts,
        "splits": splits,
    }


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfileStoreError(f"Invalid {label}")
    value = value.strip()
    if len(value) > MAX_TEXT_LENGTH:
        raise ProfileStoreError(f"The {label} is too long")
    return value


def _time(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return -1.0
    value = float(value)
    return value if math.isfinite(value) and value >= 0 else -1.0


def _clamped_int(value: Any, minimum: int, maximum: int, fallback: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return fallback
    return max(minimum, min(maximum, value))


def _clamped_float(value: Any, minimum: float, maximum: float, fallback: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return fallback
    value = float(value)
    if not math.isfinite(value):
        return fallback
    return max(minimum, min(maximum, value))
