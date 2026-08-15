"""Lazy GPU loading and drawing for BlendSplit's curated icon atlas."""

from __future__ import annotations

from pathlib import Path

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from .icon_registry import ATLAS_FILENAME, icon_uv

_image: bpy.types.Image | None = None
_owns_image = False
_texture: gpu.types.GPUTexture | None = None
_shader: gpu.types.GPUShader | None = None
_load_failed = False


def atlas_path() -> Path:
    """Return the packaged atlas path."""
    return Path(__file__).resolve().parent / "assets" / "icons" / ATLAS_FILENAME


def is_loaded() -> bool:
    return _texture is not None


def _ensure_loaded() -> bool:
    """Load the atlas only when an overlay first needs an icon."""
    global _image, _owns_image, _texture, _shader, _load_failed
    if _texture is not None and _shader is not None:
        return True
    if _load_failed:
        return False

    path = atlas_path()
    if not path.is_file():
        _load_failed = True
        print(f"BlendSplit: icon atlas is missing: {path}")
        return False

    try:
        resolved_path = str(path.resolve())
        existing = next(
            (
                image
                for image in bpy.data.images
                if bpy.path.abspath(image.filepath) == resolved_path
            ),
            None,
        )
        if existing is None:
            _image = bpy.data.images.load(resolved_path, check_existing=False)
            _image.name = "BlendSplit Icon Atlas"
            _owns_image = True
        else:
            _image = existing
            _owns_image = False
        _texture = gpu.texture.from_image(_image)
        _shader = gpu.shader.from_builtin("IMAGE")
    except Exception as error:
        print(f"BlendSplit: could not load icon atlas: {error}")
        unload()
        _load_failed = True
        return False
    return True


def draw_icon(identifier: str, x: float, y: float, size: float) -> bool:
    """Draw one atlas icon and return whether it was rendered."""
    uv = icon_uv(identifier)
    if uv is None or not _ensure_loaded():
        return False
    assert _texture is not None and _shader is not None

    u_min, v_min, u_max, v_max = uv
    positions = (
        (x, y),
        (x + size, y),
        (x + size, y + size),
        (x, y + size),
    )
    tex_coords = (
        (u_min, v_min),
        (u_max, v_min),
        (u_max, v_max),
        (u_min, v_max),
    )
    batch = batch_for_shader(
        _shader,
        "TRIS",
        {"pos": positions, "texCoord": tex_coords},
        indices=((0, 1, 2), (2, 3, 0)),
    )
    # Textures created from Blender images use premultiplied alpha. Applying
    # straight-alpha blending here multiplies translucent edge pixels twice
    # and creates a dark box/halo around otherwise transparent icon artwork.
    gpu.state.blend_set("ALPHA_PREMULT")
    try:
        _shader.uniform_sampler("image", _texture)
        batch.draw(_shader)
    finally:
        # The containing overlay uses straight alpha for panels and text.
        gpu.state.blend_set("ALPHA")
    return True


def unload() -> None:
    """Release GPU state and remove only images created by BlendSplit."""
    global _image, _owns_image, _texture, _shader, _load_failed
    _texture = None
    _shader = None
    if _owns_image and _image is not None:
        try:
            bpy.data.images.remove(_image)
        except (ReferenceError, RuntimeError):
            pass
    _image = None
    _owns_image = False
    _load_failed = False
