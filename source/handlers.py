"""Application lifecycle hooks."""

from __future__ import annotations

import bpy
from bpy.app.handlers import persistent

from . import profiles, runtime
from .icon_registry import normalize_icon


def normalize_scene_icons() -> None:
    """Migrate unsupported pre-0.5 icon identifiers to no icon."""
    # During command-line extension installation Blender may register the
    # package while bpy.data is deliberately restricted. The load handler will
    # perform the same migration as soon as regular scene data is available.
    for scene in getattr(bpy.data, "scenes", ()):
        if not hasattr(scene, "blendsplit"):
            continue
        for item in scene.blendsplit.splits:
            normalized = normalize_icon(item.blender_icon)
            if item.blender_icon != normalized:
                item.blender_icon = normalized


@persistent
def _on_load_pre(_filepath: str) -> None:
    profiles.flush_autosave()


@persistent
def _on_load_post(_filepath: str) -> None:
    # Active attempts are deliberately session-only in 0.2. A file load can
    # replace all Scene RNA, so reset cleanly instead of pairing a timer with
    # the wrong split definition.
    runtime.reset_run()
    normalize_scene_icons()
    profiles.restore_for_loaded_file()


@persistent
def _on_save_pre(_filepath: str) -> None:
    profiles.flush_autosave()


def register() -> None:
    normalize_scene_icons()
    if _on_load_pre not in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.append(_on_load_pre)
    if _on_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load_post)
    if _on_save_pre not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(_on_save_pre)


def unregister() -> None:
    if _on_save_pre in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(_on_save_pre)
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)
    if _on_load_pre in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.remove(_on_load_pre)
