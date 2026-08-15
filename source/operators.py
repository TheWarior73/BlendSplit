"""User actions exposed as Blender operators."""

from __future__ import annotations

import json
import os
from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import profiles, runtime
from .core import RunState
from .icon_registry import (
    ICON_IDS,
    ICON_ID_SET,
    icon_label,
    icon_search_text,
    normalize_icon,
)
from .runlist import RunListError, create_run_list, parse_run_list
from .random_speedruns import choose_random_challenge
from .profile_store import ProfileStoreError


_ICON_ITEMS: list[tuple[str, str, str, int, int]] | None = None


def _blender_icon_items(_self: object, _context: bpy.types.Context) -> list[tuple[str, str, str, int, int]]:
    """Return Blender's own icon enum as stable EnumProperty items."""
    global _ICON_ITEMS
    if _ICON_ITEMS is None:
        enum_items = bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items
        enum_by_identifier = {item.identifier: item for item in enum_items}
        _ICON_ITEMS = [("NONE", "No Icon", "Do not show an icon for this split", 0, 0)] + [
            (
                identifier,
                icon_label(identifier),
                f"Use the {icon_label(identifier)} icon for this split",
                enum_by_identifier[identifier].value,
                enum_by_identifier[identifier].value,
            )
            for identifier in ICON_IDS
            if identifier in enum_by_identifier
        ]
    return _ICON_ITEMS


def _editable(context: bpy.types.Context) -> bool:
    return runtime.engine.state == RunState.IDLE


class BLENDSPLIT_OT_start_split(Operator):
    bl_idname = "blendsplit.start_split"
    bl_label = "Start / Split"
    bl_description = "Start a new run or record the current split"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        settings = context.scene.blendsplit if runtime.engine.state == RunState.FINISHED else runtime.settings_for_context(context)
        return bool(settings.splits) and runtime.engine.state != RunState.PAUSED

    def execute(self, context: bpy.types.Context) -> set[str]:
        if runtime.engine.state in {RunState.IDLE, RunState.FINISHED}:
            runtime.begin_run(context.scene)
            self.report({"INFO"}, "Run started")
        else:
            settings = runtime.settings_for_context(context)
            runtime.record_split(settings)
            if runtime.engine.state == RunState.FINISHED:
                self.report({"INFO"}, "Run finished")
        return {"FINISHED"}


class BLENDSPLIT_OT_pause(Operator):
    bl_idname = "blendsplit.pause"
    bl_label = "Pause / Resume"
    bl_description = "Pause or resume the run timer"

    @classmethod
    def poll(cls, _context: bpy.types.Context) -> bool:
        return runtime.engine.is_active

    def execute(self, _context: bpy.types.Context) -> set[str]:
        runtime.engine.toggle_pause()
        runtime.tag_view3d_redraw()
        return {"FINISHED"}


class BLENDSPLIT_OT_undo(Operator):
    bl_idname = "blendsplit.undo"
    bl_label = "Undo Split"
    bl_description = "Undo the most recently recorded or skipped split"

    @classmethod
    def poll(cls, _context: bpy.types.Context) -> bool:
        return bool(runtime.engine.results)

    def execute(self, context: bpy.types.Context) -> set[str]:
        runtime.undo_split(runtime.settings_for_context(context))
        return {"FINISHED"}


class BLENDSPLIT_OT_skip(Operator):
    bl_idname = "blendsplit.skip"
    bl_label = "Skip Split"
    bl_description = "Skip the current split without recording a time"

    @classmethod
    def poll(cls, _context: bpy.types.Context) -> bool:
        return runtime.engine.state == RunState.RUNNING and runtime.engine.current_index < runtime.engine.segment_count - 1

    def execute(self, _context: bpy.types.Context) -> set[str]:
        runtime.record_skip()
        return {"FINISHED"}


class BLENDSPLIT_OT_reset(Operator):
    bl_idname = "blendsplit.reset"
    bl_label = "Reset Run"
    bl_description = "Reset the current run timer"

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        preferences = context.preferences.addons[__package__].preferences
        if runtime.engine.is_active and preferences.confirm_reset:
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def execute(self, _context: bpy.types.Context) -> set[str]:
        runtime.reset_run()
        return {"FINISHED"}


class BLENDSPLIT_OT_toggle_overlay(Operator):
    bl_idname = "blendsplit.toggle_overlay"
    bl_label = "Toggle Overlay"
    bl_description = "Show or hide the BlendSplit viewport overlay"

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = runtime.settings_for_context(context)
        settings.show_overlay = not settings.show_overlay
        return {"FINISHED"}


class BLENDSPLIT_OT_reset_ui_settings(Operator):
    bl_idname = "blendsplit.reset_ui_settings"
    bl_label = "Reset UI Settings"
    bl_description = "Restore all viewport overlay settings to their defaults"

    def execute(self, context: bpy.types.Context) -> set[str]:
        profiles.reset_ui_settings(runtime.settings_for_context(context))
        runtime.tag_view3d_redraw()
        self.report({"INFO"}, "Overlay UI settings reset")
        return {"FINISHED"}


class BLENDSPLIT_OT_save_profile(Operator):
    bl_idname = "blendsplit.save_profile"
    bl_label = "Save Speedrun Profile"
    bl_description = "Save this run setup, attempts, PBs, and best segments outside the blend file"

    as_new: bpy.props.BoolProperty(default=False, options={"HIDDEN"})

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.blendsplit
        try:
            if self.as_new or not settings.profile_id:
                title = f"{settings.run_title} Copy" if self.as_new else None
                profiles.create_profile(settings, title)
                self.report({"INFO"}, f"Created profile: {settings.run_title}")
            else:
                if not profiles.save_linked_profile(settings):
                    profiles.create_profile(settings)
                self.report({"INFO"}, f"Saved profile: {settings.run_title}")
        except ProfileStoreError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        return {"FINISHED"}


class BLENDSPLIT_OT_load_profile(Operator):
    bl_idname = "blendsplit.load_profile"
    bl_label = "Load Speedrun Profile"
    bl_description = "Load a persistent speedrun profile into this scene"

    profile_id: StringProperty(options={"HIDDEN"})

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        try:
            if not profiles.load_profile_into(context.scene.blendsplit, self.profile_id):
                self.report({"ERROR"}, "That profile no longer exists")
                return {"CANCELLED"}
        except ProfileStoreError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        runtime.tag_view3d_redraw()
        return {"FINISHED"}


class BLENDSPLIT_OT_delete_profile(Operator):
    bl_idname = "blendsplit.delete_profile"
    bl_label = "Delete Speedrun Profile"
    bl_description = "Delete the linked persistent profile while leaving this scene's current run intact"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context) and bool(context.scene.blendsplit.profile_id)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: bpy.types.Context) -> set[str]:
        try:
            if not profiles.delete_linked_profile(context.scene.blendsplit):
                self.report({"ERROR"}, "That profile no longer exists")
                return {"CANCELLED"}
        except ProfileStoreError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        self.report({"INFO"}, "Deleted profile; current scene data was kept")
        return {"FINISHED"}


class BLENDSPLIT_OT_add_split(Operator):
    bl_idname = "blendsplit.add_split"
    bl_label = "Add Split"
    bl_description = "Add a split after the selected row"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.blendsplit
        item = settings.splits.add()
        item.name = f"Split {len(settings.splits)}"
        if len(settings.splits) > 1:
            target = min(settings.active_split_index + 1, len(settings.splits) - 1)
            settings.splits.move(len(settings.splits) - 1, target)
            settings.active_split_index = target
        else:
            settings.active_split_index = 0
        profiles.schedule_autosave(settings)
        runtime.tag_view3d_redraw()
        return {"FINISHED"}


class BLENDSPLIT_OT_add_starter_splits(Operator):
    bl_idname = "blendsplit.add_starter_splits"
    bl_label = "Create Starter Splits"
    bl_description = "Create a small example split list"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context) and not context.scene.blendsplit.splits

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.blendsplit
        for name in ("Start", "Main Task", "Finish"):
            item = settings.splits.add()
            item.name = name
        settings.active_split_index = 0
        profiles.schedule_autosave(settings)
        runtime.tag_view3d_redraw()
        return {"FINISHED"}


class BLENDSPLIT_OT_random_speedrun(Operator):
    bl_idname = "blendsplit.random_speedrun"
    bl_label = "Get Random Speedrun"
    bl_description = "Replace the current setup with one of ten fun five-split Blender challenges"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.blendsplit
        profiles.unlink_profile(settings)
        challenge = choose_random_challenge(settings.run_title)
        settings.run_title = challenge.title
        settings.category = challenge.category
        settings.splits.clear()
        for name, icon in challenge.splits:
            item = settings.splits.add()
            item.name = name
            item.blender_icon = icon
        settings.active_split_index = 0
        profiles.schedule_autosave(settings)
        runtime.tag_view3d_redraw()
        self.report({"INFO"}, f"Random challenge: {challenge.title}")
        return {"FINISHED"}


class BLENDSPLIT_OT_remove_split(Operator):
    bl_idname = "blendsplit.remove_split"
    bl_label = "Remove Split"
    bl_description = "Remove the selected split"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context) and bool(context.scene.blendsplit.splits)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.blendsplit
        index = min(settings.active_split_index, len(settings.splits) - 1)
        settings.splits.remove(index)
        settings.active_split_index = max(0, min(index, len(settings.splits) - 1))
        profiles.schedule_autosave(settings)
        runtime.tag_view3d_redraw()
        return {"FINISHED"}


class BLENDSPLIT_OT_move_split(Operator):
    bl_idname = "blendsplit.move_split"
    bl_label = "Move Split"
    bl_description = "Move the selected split up or down"

    direction: bpy.props.EnumProperty(items=(("UP", "Up", ""), ("DOWN", "Down", "")))

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context) and len(context.scene.blendsplit.splits) > 1

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.blendsplit
        old = min(settings.active_split_index, len(settings.splits) - 1)
        new = old - 1 if self.direction == "UP" else old + 1
        new = max(0, min(new, len(settings.splits) - 1))
        if new != old:
            settings.splits.move(old, new)
            settings.active_split_index = new
            profiles.schedule_autosave(settings)
        runtime.tag_view3d_redraw()
        return {"FINISHED"}


class BLENDSPLIT_OT_choose_icon(Operator):
    bl_idname = "blendsplit.choose_icon"
    bl_label = "Choose Blender Icon"
    bl_description = "Choose an optional split icon supported in both the panel and overlay"
    bl_options = {"INTERNAL"}

    split_index: bpy.props.IntProperty(
        name="Split Index",
        description="Split receiving the selected icon",
        default=0,
        min=0,
        options={"HIDDEN"},
    )
    icon_choice: bpy.props.EnumProperty(name="Icon", items=_blender_icon_items)
    icon_filter: bpy.props.StringProperty(
        name="Search",
        description="Filter supported icons by name or group",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context) and bool(context.scene.blendsplit.splits)

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        settings = context.scene.blendsplit
        if self.split_index >= len(settings.splits):
            return {"CANCELLED"}
        current = settings.splits[self.split_index].blender_icon
        identifiers = {item[0] for item in _blender_icon_items(self, context)}
        self.icon_choice = current if current in identifiers else "NONE"
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "icon_filter", text="", icon="VIEWZOOM")
        layout.prop_enum(self, "icon_choice", "NONE", text="No Icon", icon="X")

        query = self.icon_filter.strip().upper()
        items = [
            item for item in _blender_icon_items(self, context)
            if item[0] != "NONE" and (not query or query in icon_search_text(item[0]))
        ]
        grid = layout.grid_flow(row_major=True, columns=12, even_columns=True, even_rows=True, align=True)
        for identifier, _name, _description, _icon_value, _number in items:
            grid.prop_enum(self, "icon_choice", identifier, text="", icon=identifier)

        if not items:
            layout.label(text="No matching icons", icon="INFO")

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.blendsplit
        if self.split_index < len(settings.splits):
            settings.splits[self.split_index].blender_icon = self.icon_choice
        else:
            self.report({"ERROR"}, "That split no longer exists")
            return {"CANCELLED"}
        runtime.tag_view3d_redraw()
        return {"FINISHED"}


class BLENDSPLIT_OT_export_list(Operator, ExportHelper):
    bl_idname = "blendsplit.export_list"
    bl_label = "Export Run List"
    bl_description = "Export the run title, category, ordered splits, and split icons to JSON"
    bl_options = {"INTERNAL"}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context) and bool(context.scene.blendsplit.splits)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        if not self.filepath:
            clean_title = bpy.path.clean_name(context.scene.blendsplit.run_title) or "blendsplit-run"
            self.filepath = f"{clean_title}.blendsplit.json"
        return ExportHelper.invoke(self, context, event)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.blendsplit
        payload = create_run_list(
            settings.run_title,
            settings.category,
            ((item.name, normalize_icon(item.blender_icon)) for item in settings.splits),
        )
        destination = Path(self.filepath)
        temporary = destination.with_name(destination.name + ".tmp")
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temporary, destination)
        except OSError as error:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            self.report({"ERROR"}, f"Could not export run list: {error}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Exported {len(settings.splits)} splits")
        return {"FINISHED"}


class BLENDSPLIT_OT_import_list(Operator, ImportHelper):
    bl_idname = "blendsplit.import_list"
    bl_label = "Import Run List"
    bl_description = "Replace the current setup with a BlendSplit JSON run list"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        source = Path(self.filepath)
        try:
            if source.stat().st_size > 2_000_000:
                raise RunListError("The run-list file is unexpectedly large")
            with source.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            title, category, splits = parse_run_list(payload, set(ICON_ID_SET) | {"NONE"})
        except (OSError, UnicodeError, json.JSONDecodeError, RunListError) as error:
            self.report({"ERROR"}, f"Could not import run list: {error}")
            return {"CANCELLED"}

        settings = context.scene.blendsplit
        profiles.unlink_profile(settings)
        settings.run_title = title
        settings.category = category
        settings.splits.clear()
        for name, icon in splits:
            item = settings.splits.add()
            item.name = name
            item.blender_icon = icon
        settings.active_split_index = 0
        profiles.schedule_autosave(settings)
        runtime.tag_view3d_redraw()
        self.report({"INFO"}, f"Imported {len(splits)} splits")
        return {"FINISHED"}


class BLENDSPLIT_OT_clear_pb(Operator):
    bl_idname = "blendsplit.clear_pb"
    bl_label = "Clear PB and Best Segments"
    bl_description = "Clear the personal best and best-segment times without changing the attempt count"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return _editable(context) and bool(context.scene.blendsplit.splits)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.blendsplit
        for item in settings.splits:
            item.pb_time = -1.0
            item.best_segment = -1.0
        profiles.schedule_autosave(settings)
        runtime.tag_view3d_redraw()
        return {"FINISHED"}


CLASSES = (
    BLENDSPLIT_OT_start_split,
    BLENDSPLIT_OT_pause,
    BLENDSPLIT_OT_undo,
    BLENDSPLIT_OT_skip,
    BLENDSPLIT_OT_reset,
    BLENDSPLIT_OT_toggle_overlay,
    BLENDSPLIT_OT_reset_ui_settings,
    BLENDSPLIT_OT_save_profile,
    BLENDSPLIT_OT_load_profile,
    BLENDSPLIT_OT_delete_profile,
    BLENDSPLIT_OT_add_split,
    BLENDSPLIT_OT_add_starter_splits,
    BLENDSPLIT_OT_random_speedrun,
    BLENDSPLIT_OT_remove_split,
    BLENDSPLIT_OT_move_split,
    BLENDSPLIT_OT_choose_icon,
    BLENDSPLIT_OT_export_list,
    BLENDSPLIT_OT_import_list,
    BLENDSPLIT_OT_clear_pb,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
