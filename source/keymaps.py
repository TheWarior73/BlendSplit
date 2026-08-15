"""Default BlendSplit keyboard shortcuts."""

from __future__ import annotations

import bpy


_addon_keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


def register() -> None:
    keyconfig = bpy.context.window_manager.keyconfigs.addon
    if keyconfig is None:
        return
    keymap = keyconfig.keymaps.new(name="Window", space_type="EMPTY", region_type="WINDOW")
    bindings = (
        ("blendsplit.start_split", "ONE"),
        ("blendsplit.pause", "TWO"),
        ("blendsplit.undo", "THREE"),
        ("blendsplit.skip", "FOUR"),
        ("blendsplit.reset", "FIVE"),
        ("blendsplit.toggle_overlay", "SIX"),
    )
    for operator, key in bindings:
        item = keymap.keymap_items.new(operator, key, "PRESS", ctrl=True, shift=True, alt=True)
        _addon_keymaps.append((keymap, item))


def unregister() -> None:
    for keymap, item in _addon_keymaps:
        try:
            keymap.keymap_items.remove(item)
        except (ReferenceError, RuntimeError):
            pass
    _addon_keymaps.clear()
