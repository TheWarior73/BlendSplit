"""Foreground Blender smoke test for UI-only operator invocation paths."""

from __future__ import annotations

import importlib
import pathlib
import sys

import bpy


ROOT = pathlib.Path(__file__).resolve().parents[1]
PARENT = str(ROOT.parent)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

addon = importlib.import_module(ROOT.name)
addon.register()


def invoke_icon_picker() -> None:
    settings = bpy.context.scene.blendsplit
    item = settings.splits.add()
    item.name = "UI Smoke Split"
    result = bpy.ops.blendsplit.choose_icon("INVOKE_DEFAULT", split_index=0)
    assert result == {"RUNNING_MODAL"}, result
    print("BLENDSPLIT_ICON_PICKER_INVOKE_OK")
    bpy.app.timers.register(quit_blender, first_interval=0.1)
    return None


def quit_blender() -> None:
    bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(invoke_icon_picker, first_interval=0.1)
