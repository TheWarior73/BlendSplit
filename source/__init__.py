"""BlendSplit — Live speedrun timing inside Blender."""

from __future__ import annotations

bl_info = {
    "name": "BlendSplit",
    "author": "Polyfjord",
    "version": (1, 2, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Sidebar > Speedrun",
    "description": "Live speedrun splits inside the 3D Viewport",
    "category": "3D View",
}

from . import handlers, keymaps, operators, overlay, panels, profiles, properties, runtime


def register() -> None:
    properties.register()
    operators.register()
    panels.register()
    overlay.register()
    handlers.register()
    keymaps.register()
    runtime.register_timer()


def unregister() -> None:
    profiles.shutdown()
    runtime.unregister_timer()
    keymaps.unregister()
    handlers.unregister()
    overlay.unregister()
    panels.unregister()
    operators.unregister()
    properties.unregister()
