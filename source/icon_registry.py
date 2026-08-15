"""Curated Blender 5.2 icon registry shared by the picker and overlay."""

from __future__ import annotations

ATLAS_COLUMNS = 10
ATLAS_ROWS = 10
ATLAS_TILE_SIZE = 64
ATLAS_FILENAME = "blendsplit_icons.png"

# The order is part of the atlas format. Do not reorder without regenerating
# assets/icons/blendsplit_icons.png with tools/generate_icon_atlas.py.
ICON_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "General",
        (
            "CHECKMARK", "CANCEL", "ERROR", "INFO", "QUESTION", "ADD",
            "REMOVE", "DUPLICATE", "TRASH", "LOCKED", "UNLOCKED",
        ),
    ),
    (
        "Primitives",
        (
            "MESH_CUBE", "MESH_PLANE", "MESH_CIRCLE", "MESH_UVSPHERE",
            "MESH_ICOSPHERE", "MESH_GRID", "MESH_MONKEY", "MESH_CYLINDER",
            "MESH_CONE", "MESH_TORUS",
        ),
    ),
    (
        "Objects",
        (
            "OBJECT_DATA", "MESH_DATA", "CURVE_DATA", "SURFACE_DATA",
            "META_DATA", "FONT_DATA", "ARMATURE_DATA", "LATTICE_DATA",
            "CAMERA_DATA", "LIGHT_DATA", "EMPTY_DATA", "SPEAKER",
            "VOLUME_DATA", "POINTCLOUD_DATA", "CURVES_DATA", "GREASEPENCIL",
        ),
    ),
    (
        "Modeling",
        (
            "EDITMODE_HLT", "VERTEXSEL", "EDGESEL", "FACESEL", "PIVOT_CURSOR",
            "PIVOT_ACTIVE", "PIVOT_MEDIAN", "ORIENTATION_GLOBAL",
            "ORIENTATION_LOCAL", "ORIENTATION_NORMAL", "SNAP_ON", "SNAP_VERTEX",
            "SNAP_EDGE", "SNAP_FACE",
        ),
    ),
    (
        "Sculpt and Paint",
        (
            "SCULPTMODE_HLT", "TPAINT_HLT", "VPAINT_HLT", "WPAINT_HLT",
            "BRUSH_DATA", "EYEDROPPER", "COLOR",
        ),
    ),
    (
        "Materials and Nodes",
        (
            "MATERIAL", "MATERIAL_DATA", "TEXTURE", "NODETREE",
            "NODE_MATERIAL", "MODIFIER", "MODIFIER_DATA",
        ),
    ),
    (
        "Animation",
        (
            "ANIM", "ACTION", "KEYFRAME", "NEXT_KEYFRAME", "PREV_KEYFRAME",
            "PLAY", "PAUSE", "REC", "MARKER", "NLA",
        ),
    ),
    (
        "Render and Shading",
        (
            "RENDER_STILL", "RENDER_ANIMATION", "RENDER_RESULT", "RENDERLAYERS",
            "SHADING_RENDERED", "SHADING_SOLID", "SHADING_WIRE",
        ),
    ),
    (
        "Files",
        (
            "FILE_NEW", "FILE_TICK", "FILE_FOLDER", "FILE_REFRESH", "FILE_BLEND",
            "FILE_IMAGE", "IMPORT", "EXPORT",
        ),
    ),
    (
        "Navigation",
        (
            "HOME", "VIEW_CAMERA", "VIEW_PERSPECTIVE", "VIEW_ORTHO", "VIEW_PAN",
            "VIEW_ZOOM", "ZOOM_ALL", "ZOOM_SELECTED", "HIDE_OFF", "SOLO_ON",
        ),
    ),
)

ICON_IDS: tuple[str, ...] = tuple(
    identifier
    for _group, identifiers in ICON_GROUPS
    for identifier in identifiers
)
ICON_ID_SET = frozenset(ICON_IDS)
ICON_INDEX = {identifier: index for index, identifier in enumerate(ICON_IDS)}
ICON_GROUP_BY_ID = {
    identifier: group
    for group, identifiers in ICON_GROUPS
    for identifier in identifiers
}


def icon_label(identifier: str) -> str:
    """Return a compact human-readable name for an icon identifier."""
    return identifier.removesuffix("_HLT").replace("_", " ").title()


def icon_search_text(identifier: str) -> str:
    """Return normalized picker search text including the icon's group."""
    return f"{identifier} {icon_label(identifier)} {ICON_GROUP_BY_ID[identifier]}".upper()


def normalize_icon(identifier: str | None) -> str:
    """Return a supported icon identifier or the no-icon sentinel."""
    return identifier if identifier in ICON_ID_SET else "NONE"


def icon_uv(identifier: str) -> tuple[float, float, float, float] | None:
    """Return bottom-left UV bounds for an icon in the atlas."""
    index = ICON_INDEX.get(identifier)
    if index is None:
        return None
    column = index % ATLAS_COLUMNS
    row_from_top = index // ATLAS_COLUMNS
    u_min = column / ATLAS_COLUMNS
    u_max = (column + 1) / ATLAS_COLUMNS
    v_min = 1.0 - ((row_from_top + 1) / ATLAS_ROWS)
    v_max = 1.0 - (row_from_top / ATLAS_ROWS)
    return u_min, v_min, u_max, v_max
