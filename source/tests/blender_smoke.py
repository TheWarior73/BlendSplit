"""Headless Blender registration and operator smoke test."""

from __future__ import annotations

import importlib
import pathlib
import sys
import tempfile
from types import SimpleNamespace

import bpy


ROOT = pathlib.Path(__file__).resolve().parents[1]
PARENT = str(ROOT.parent)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

addon = importlib.import_module(ROOT.name)
addon.register()

profile_directory = pathlib.Path(tempfile.mkdtemp(prefix="blendsplit-profile-smoke-"))
addon.profiles.profile_library_path = lambda: profile_directory / "profiles.json"

try:
    assert addon.panels.BLENDSPLIT_PT_profile.bl_label == "Profile"
    assert addon.panels.BLENDSPLIT_PT_profile.bl_options == {"DEFAULT_CLOSED"}
    assert not hasattr(addon.panels, "BLENDSPLIT_PT_transfer")
    settings = bpy.context.scene.blendsplit
    assert settings.run_title == "Untitled Blender Run"
    bpy.ops.blendsplit.add_starter_splits()
    assert len(settings.splits) == 3
    assert not hasattr(settings.splits[0], "icon")
    assert all(item.blender_icon == "NONE" for item in settings.splits)
    assert settings.overlay_width == 285
    assert settings.overlay_offset_y == 100
    assert settings.show_attempts
    assert settings.show_pb

    # Global overlay preferences persist independently of a saved run profile.
    settings.show_overlay = False
    settings.show_attempts = False
    settings.overlay_anchor = "BOTTOM_RIGHT"
    settings.overlay_offset_x = 77
    settings.overlay_scale = 1.6
    settings.overlay_width = 390
    addon.profiles.flush_autosave()
    stored_ui = addon.profiles.library()
    assert stored_ui["ui_settings_initialized"]
    assert stored_ui["ui_settings"]["show_overlay"] is False
    assert stored_ui["ui_settings"]["overlay_width"] == 390
    with addon.profiles.suspend_autosave():
        settings.show_overlay = True
        settings.show_attempts = True
        settings.overlay_anchor = "TOP_LEFT"
        settings.overlay_offset_x = 18
        settings.overlay_scale = 1.0
        settings.overlay_width = 285
    addon.profiles.restore_ui_settings(settings)
    assert settings.show_overlay is False
    assert settings.show_attempts is False
    assert settings.overlay_anchor == "BOTTOM_RIGHT"
    assert settings.overlay_offset_x == 77
    assert abs(settings.overlay_scale - 1.6) < 0.00001
    assert settings.overlay_width == 390
    assert bpy.ops.blendsplit.reset_ui_settings() == {"FINISHED"}
    assert settings.show_overlay
    assert settings.show_attempts
    assert settings.show_pb
    assert settings.overlay_anchor == "TOP_LEFT"
    assert settings.overlay_offset_x == 18
    assert settings.overlay_offset_y == 100
    assert abs(settings.overlay_scale - 1.0) < 0.00001
    assert settings.overlay_width == 285

    expected_shortcuts = {
        "blendsplit.start_split": "ONE",
        "blendsplit.pause": "TWO",
        "blendsplit.undo": "THREE",
        "blendsplit.skip": "FOUR",
        "blendsplit.reset": "FIVE",
        "blendsplit.toggle_overlay": "SIX",
    }
    assert len(addon.keymaps._addon_keymaps) == len(expected_shortcuts)
    for _keymap, item in addon.keymaps._addon_keymaps:
        assert expected_shortcuts[item.idname] == item.type
        assert item.ctrl and item.shift and item.alt
        assert not item.oskey
    assert bpy.ops.blendsplit.random_speedrun() == {"FINISHED"}
    first_random_title = settings.run_title
    assert len(settings.splits) == 5
    assert all(item.blender_icon in addon.icon_registry.ICON_ID_SET for item in settings.splits)
    assert bpy.ops.blendsplit.random_speedrun() == {"FINISHED"}
    assert settings.run_title != first_random_title
    assert len(settings.splits) == 5
    settings.splits.clear()
    bpy.ops.blendsplit.add_starter_splits()
    # A first run has no comparison PB, even after it saves its result as PB.
    assert all(item.pb_time < 0 for item in settings.splits)
    addon.runtime.begin_run(bpy.context.scene)
    assert all(addon.runtime.comparison_pb_time(index) < 0 for index in range(3))
    for _index in range(3):
        addon.runtime.record_split(settings)
    assert all(item.pb_time >= 0 for item in settings.splits)
    assert all(addon.runtime.comparison_pb_time(index) < 0 for index in range(3))
    addon.runtime.reset_run()
    settings.attempts = 0
    for item in settings.splits:
        item.pb_time = -1.0
    assert bpy.ops.blendsplit.choose_icon(
        "EXEC_DEFAULT",
        split_index=0,
        icon_choice="MESH_CUBE",
    ) == {"FINISHED"}
    assert settings.splits[0].blender_icon == "MESH_CUBE"
    settings.splits[1].blender_icon = "EVENT_F12"
    addon.handlers.normalize_scene_icons()
    assert settings.splits[1].blender_icon == "NONE"
    assert "page" not in bpy.ops.blendsplit.choose_icon.get_rna_type().properties
    picker_ids = [item[0] for item in addon.operators._blender_icon_items(None, bpy.context)]
    assert len(picker_ids) == 101
    assert picker_ids[0] == "NONE"
    assert set(picker_ids[1:]) == set(addon.icon_registry.ICON_IDS)
    assert not hasattr(settings, "category_icon")
    assert not hasattr(settings, "completed_runs")
    settings.attempts = 41
    settings.overall_pb = 83.45
    assert abs(settings.splits[-1].pb_time - 83.45) < 0.00001
    addon.runtime.begin_run(bpy.context.scene)
    assert abs(addon.runtime.comparison_pb_time(2) - 83.45) < 0.00001
    settings.splits[-1].pb_time = 12.0
    assert abs(addon.runtime.comparison_pb_time(2) - 83.45) < 0.00001
    addon.runtime.reset_run()
    settings.attempts = 41

    transfer_path = pathlib.Path(tempfile.gettempdir()) / "blendsplit-smoke-run-list.json"
    settings.run_title = "Smoke Run"
    settings.category = "No Add-ons"
    assert bpy.ops.blendsplit.export_list("EXEC_DEFAULT", filepath=str(transfer_path)) == {"FINISHED"}
    settings.run_title = "Changed"
    settings.splits.clear()
    assert bpy.ops.blendsplit.import_list("EXEC_DEFAULT", filepath=str(transfer_path)) == {"FINISHED"}
    assert settings.run_title == "Smoke Run"
    assert settings.category == "No Add-ons"
    assert [item.name for item in settings.splits] == ["Start", "Main Task", "Finish"]
    assert settings.splits[0].blender_icon == "MESH_CUBE"
    assert settings.attempts == 41
    transfer_path.unlink(missing_ok=True)

    # Persistent profiles keep setup and statistics outside the blend file.
    assert not settings.profile_id
    assert bpy.ops.blendsplit.save_profile() == {"FINISHED"}
    original_profile_id = settings.profile_id
    assert original_profile_id
    stored = addon.profiles.library()["profiles"][original_profile_id]
    assert stored["title"] == "Smoke Run"
    assert stored["attempts"] == 41
    settings.attempts = 52
    settings.splits[0].best_segment = 1.25
    addon.profiles.schedule_autosave(settings)
    addon.profiles.flush_autosave()
    stored = addon.profiles.library()["profiles"][original_profile_id]
    assert stored["attempts"] == 52
    assert abs(stored["splits"][0]["best_segment"] - 1.25) < 0.00001

    assert bpy.ops.blendsplit.save_profile(as_new=True) == {"FINISHED"}
    duplicate_profile_id = settings.profile_id
    assert duplicate_profile_id != original_profile_id
    assert settings.run_title == "Smoke Run Copy"
    assert len(addon.profiles.all_profiles()) == 2
    assert bpy.ops.blendsplit.delete_profile("EXEC_DEFAULT") == {"FINISHED"}
    assert not settings.profile_id
    assert len(addon.profiles.all_profiles()) == 1
    assert bpy.ops.blendsplit.load_profile(profile_id=original_profile_id) == {"FINISHED"}
    assert settings.run_title == "Smoke Run"
    assert settings.attempts == 52
    assert settings.profile_id == original_profile_id
    assert bpy.ops.blendsplit.random_speedrun() == {"FINISHED"}
    assert not settings.profile_id
    assert addon.profiles.library()["profiles"][original_profile_id]["title"] == "Smoke Run"
    assert bpy.ops.blendsplit.load_profile(profile_id=original_profile_id) == {"FINISHED"}

    # Anchor math remains inside the region at normal and high-DPI scales.
    for scale in (1.0, 2.0):
        width, height = 285 * scale, 320 * scale
        for anchor in ("TOP_LEFT", "TOP_RIGHT", "BOTTOM_LEFT", "BOTTOM_RIGHT"):
            inset = 78 * scale if anchor.endswith("LEFT") else 0
            x, y = addon.overlay._overlay_position(1920, 1080, anchor, 18 * scale, 100 * scale, width, height, inset)
            assert 0 <= x <= 1920 - width
            assert 0 <= y <= 1080 - height
            if anchor.endswith("LEFT"):
                assert x == 18 * scale + inset
    hidden_toolbar = SimpleNamespace(regions=[SimpleNamespace(type="TOOLS", width=1)])
    visible_toolbar = SimpleNamespace(regions=[SimpleNamespace(type="TOOLS", width=70)])
    assert addon.overlay._visible_toolbar_width(hidden_toolbar) == 0
    assert addon.overlay._visible_toolbar_width(visible_toolbar) == 70
    # Empty time columns no longer impose the old fixed 58% label cap.
    assert addon.overlay._row_label_width(330, 13, 23, 0, 1) == 281
    assert addon.overlay._row_label_width(460, 13, 23, 0, 1) == 411
    assert addon.overlay._row_label_width(330, 13, 23, 70, 1) == 201

    # The packaged atlas can be decoded by Blender and cleanup removes only
    # the image explicitly owned by the extension.
    atlas = bpy.data.images.load(str(addon.icon_atlas.atlas_path()), check_existing=False)
    assert tuple(atlas.size) == (640, 640)
    atlas_name = atlas.name
    addon.icon_atlas._image = atlas
    addon.icon_atlas._owns_image = True
    addon.icon_atlas.unload()
    assert atlas_name not in bpy.data.images

    shared_atlas = bpy.data.images.load(str(addon.icon_atlas.atlas_path()), check_existing=False)
    shared_name = shared_atlas.name
    addon.icon_atlas._image = shared_atlas
    addon.icon_atlas._owns_image = False
    addon.icon_atlas.unload()
    assert shared_name in bpy.data.images
    bpy.data.images.remove(shared_atlas)

    original_atlas_path = addon.icon_atlas.atlas_path
    addon.icon_atlas.atlas_path = lambda: ROOT / "assets" / "icons" / "missing.png"
    try:
        assert not addon.icon_atlas.draw_icon("MESH_CUBE", 0, 0, 16)
    finally:
        addon.icon_atlas.atlas_path = original_atlas_path
        addon.icon_atlas.unload()

    assert bpy.ops.blendsplit.start_split() == {"FINISHED"}
    assert settings.attempts == 53
    assert addon.profiles.library()["profiles"][original_profile_id]["attempts"] == 53
    assert addon.runtime.engine.is_active
    assert bpy.ops.blendsplit.pause() == {"FINISHED"}
    assert addon.runtime.engine.state.value == "PAUSED"
    assert bpy.ops.blendsplit.pause() == {"FINISHED"}
    assert bpy.ops.blendsplit.skip() == {"FINISHED"}
    assert bpy.ops.blendsplit.undo() == {"FINISHED"}
    assert bpy.ops.blendsplit.reset("EXEC_DEFAULT") == {"FINISHED"}
    assert addon.runtime.engine.state.value == "IDLE"

    for property_name in (
        "run_title",
        "category",
        "attempts",
        "overall_pb",
        "show_overlay",
        "show_attempts",
        "show_pb",
        "overlay_width",
    ):
        assert addon.properties.BlendSplitSettings.bl_rna.properties[property_name].description
    print("BLENDSPLIT_SMOKE_OK")
finally:
    addon.unregister()

assert not hasattr(bpy.types.Scene, "blendsplit")
print("BLENDSPLIT_UNREGISTER_OK")
