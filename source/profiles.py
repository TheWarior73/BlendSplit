"""Blender integration for persistent BlendSplit speedrun profiles."""

from __future__ import annotations

import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import bpy

from .icon_registry import ICON_ID_SET, normalize_icon
from .profile_store import DEFAULT_UI_SETTINGS, ProfileStoreError, load_library, save_library


_autosave_scene_name: str | None = None
_ui_autosave_scene_name: str | None = None
_suspend_depth = 0


def profile_library_path() -> Path:
    directory = bpy.utils.user_resource("CONFIG", path="blendsplit", create=True)
    return Path(directory) / "profiles.json"


def library() -> dict:
    return load_library(profile_library_path(), set(ICON_ID_SET) | {"NONE"})


def all_profiles() -> list[dict]:
    values = library()["profiles"].values()
    return sorted(values, key=lambda profile: profile["title"].casefold())


def active_profile() -> dict | None:
    data = library()
    return data["profiles"].get(data["active_profile_id"])


def linked_profile(settings: object) -> dict | None:
    profile_id = getattr(settings, "profile_id", "")
    return library()["profiles"].get(profile_id)


def create_profile(settings: object, title: str | None = None) -> str:
    flush_autosave()
    if title is not None:
        with suspend_autosave():
            settings.run_title = title
    data = library()
    profile_id = uuid.uuid4().hex
    profile = _settings_payload(settings, profile_id, revision=1)
    data["profiles"][profile_id] = profile
    data["active_profile_id"] = profile_id
    _save(data)
    with suspend_autosave():
        settings.profile_id = profile_id
        settings.profile_revision = 1
    return profile_id


def save_linked_profile(settings: object) -> bool:
    profile_id = getattr(settings, "profile_id", "")
    if not profile_id:
        return False
    data = library()
    old = data["profiles"].get(profile_id)
    if old is None:
        with suspend_autosave():
            settings.profile_id = ""
            settings.profile_revision = 0
        return False
    revision = int(old.get("revision", 0)) + 1
    data["profiles"][profile_id] = _settings_payload(settings, profile_id, revision)
    data["active_profile_id"] = profile_id
    _save(data)
    with suspend_autosave():
        settings.profile_revision = revision
    return True


def load_profile_into(settings: object, profile_id: str) -> bool:
    flush_autosave()
    data = library()
    profile = data["profiles"].get(profile_id)
    if profile is None:
        return False
    _apply_profile(settings, profile)
    data["active_profile_id"] = profile_id
    _save(data)
    return True


def delete_linked_profile(settings: object) -> bool:
    flush_autosave()
    profile_id = getattr(settings, "profile_id", "")
    if not profile_id:
        return False
    data = library()
    if profile_id not in data["profiles"]:
        return False
    del data["profiles"][profile_id]
    if data["active_profile_id"] == profile_id:
        data["active_profile_id"] = next(iter(data["profiles"]), "")
    _save(data)
    with suspend_autosave():
        settings.profile_id = ""
        settings.profile_revision = 0
    return True


def unlink_profile(settings: object) -> None:
    """Keep the scene's run data but stop syncing it to a saved profile."""
    flush_autosave()
    with suspend_autosave():
        settings.profile_id = ""
        settings.profile_revision = 0


def schedule_autosave(settings: object) -> None:
    global _autosave_scene_name
    if _suspend_depth or not getattr(settings, "profile_id", ""):
        return
    scene = getattr(settings, "id_data", None)
    _autosave_scene_name = getattr(scene, "name", None)
    if not bpy.app.timers.is_registered(_autosave_timer):
        bpy.app.timers.register(_autosave_timer, first_interval=0.5)


def schedule_ui_autosave(settings: object) -> None:
    global _ui_autosave_scene_name
    if _suspend_depth:
        return
    scene = getattr(settings, "id_data", None)
    _ui_autosave_scene_name = getattr(scene, "name", None)
    if not bpy.app.timers.is_registered(_autosave_timer):
        bpy.app.timers.register(_autosave_timer, first_interval=0.5)


def flush_autosave() -> None:
    global _autosave_scene_name, _ui_autosave_scene_name
    scene_name = _autosave_scene_name
    ui_scene_name = _ui_autosave_scene_name
    _autosave_scene_name = None
    _ui_autosave_scene_name = None
    try:
        scene = getattr(bpy.data, "scenes", {}).get(scene_name) if scene_name else None
        if scene is not None and hasattr(scene, "blendsplit"):
            save_linked_profile(scene.blendsplit)
        ui_scene = getattr(bpy.data, "scenes", {}).get(ui_scene_name) if ui_scene_name else None
        if ui_scene is not None and hasattr(ui_scene, "blendsplit"):
            save_ui_settings(ui_scene.blendsplit)
    except ProfileStoreError as error:
        print(f"BlendSplit: could not auto-save settings: {error}")


def save_ui_settings(settings: object) -> None:
    data = library()
    data["ui_settings"] = _ui_payload(settings)
    data["ui_settings_initialized"] = True
    _save(data)


def restore_ui_settings(settings: object) -> None:
    data = library()
    if not data["ui_settings_initialized"]:
        # On the first v1.2 load, preserve any overlay choices embedded in the
        # user's current file instead of replacing them with defaults.
        data["ui_settings"] = _ui_payload(settings)
        data["ui_settings_initialized"] = True
        _save(data)
        return
    _apply_ui_settings(settings, data["ui_settings"])


def reset_ui_settings(settings: object) -> None:
    _apply_ui_settings(settings, DEFAULT_UI_SETTINGS)
    save_ui_settings(settings)


def restore_for_loaded_file() -> bool:
    """Restore linked files, or the last profile for a fresh unsaved file."""
    scene = getattr(bpy.context, "scene", None)
    if scene is None or not hasattr(scene, "blendsplit"):
        return False
    settings = scene.blendsplit
    restore_ui_settings(settings)
    if settings.profile_id:
        if load_profile_into(settings, settings.profile_id):
            return True
        # A file copied from another computer can reference a profile that is
        # not in this installation. Keep its embedded run data, but mark it as
        # unlinked instead of pretending autosave is active.
        unlink_profile(settings)
        return False
    if bpy.data.filepath or not _auto_load_enabled():
        return False
    profile = active_profile()
    return bool(profile and load_profile_into(settings, profile["id"]))


def shutdown() -> None:
    global _autosave_scene_name, _ui_autosave_scene_name
    flush_autosave()
    _autosave_scene_name = None
    _ui_autosave_scene_name = None
    if bpy.app.timers.is_registered(_autosave_timer):
        bpy.app.timers.unregister(_autosave_timer)


def _autosave_timer() -> None:
    flush_autosave()
    return None


def _settings_payload(settings: object, profile_id: str, revision: int) -> dict:
    return {
        "id": profile_id,
        "revision": revision,
        "title": settings.run_title,
        "category": settings.category,
        "attempts": settings.attempts,
        "splits": [
            {
                "name": item.name,
                "blender_icon": normalize_icon(item.blender_icon),
                "pb_time": item.pb_time,
                "best_segment": item.best_segment,
            }
            for item in settings.splits
        ],
    }


def _ui_payload(settings: object) -> dict:
    return {name: getattr(settings, name) for name in DEFAULT_UI_SETTINGS}


def _apply_profile(settings: object, profile: dict) -> None:
    with suspend_autosave():
        settings.run_title = profile["title"]
        settings.category = profile["category"]
        settings.attempts = profile["attempts"]
        settings.splits.clear()
        for split in profile["splits"]:
            item = settings.splits.add()
            item.name = split["name"]
            item.blender_icon = normalize_icon(split["blender_icon"])
            item.pb_time = split["pb_time"]
            item.best_segment = split["best_segment"]
        settings.active_split_index = 0
        settings.profile_id = profile["id"]
        settings.profile_revision = profile["revision"]


def _apply_ui_settings(settings: object, values: dict) -> None:
    with suspend_autosave():
        for name in DEFAULT_UI_SETTINGS:
            setattr(settings, name, values[name])


def _save(data: dict) -> None:
    save_library(profile_library_path(), data, set(ICON_ID_SET) | {"NONE"})


def _auto_load_enabled() -> bool:
    addon = bpy.context.preferences.addons.get(__package__)
    return addon is None or addon.preferences.auto_load_last_profile


@contextmanager
def suspend_autosave() -> Iterator[None]:
    global _suspend_depth
    _suspend_depth += 1
    try:
        yield
    finally:
        _suspend_depth -= 1
