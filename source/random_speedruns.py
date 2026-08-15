"""Hand-authored speedrun challenges for BlendSplit's randomizer."""

from __future__ import annotations

import random
from typing import NamedTuple


class Challenge(NamedTuple):
    title: str
    category: str
    splits: tuple[tuple[str, str], ...]


CHALLENGES: tuple[Challenge, ...] = (
    Challenge(
        "Primitive Parade",
        "Glitchless • Beginner",
        (
            ("Cube, Plane & Grid", "MESH_CUBE"),
            ("Circle, Cylinder & Cone", "MESH_CYLINDER"),
            ("Two Kinds of Sphere", "MESH_UVSPHERE"),
            ("Torus & Suzanne", "MESH_MONKEY"),
            ("Arrange the Collection", "OBJECT_DATA"),
        ),
    ),
    Challenge(
        "25 Monkeys in a Circle",
        "Any% • Beginner",
        (
            ("Create Suzanne", "MESH_MONKEY"),
            ("Make a 25-Monkey Ring", "DUPLICATE"),
            ("Face Them Inward", "PIVOT_CURSOR"),
            ("Add Three Materials", "MATERIAL"),
            ("Frame and Render", "RENDER_STILL"),
        ),
    ),
    Challenge(
        "Low-Poly Car",
        "Glitchless • Advanced",
        (
            ("Block Out the Body", "MESH_CUBE"),
            ("Build Four Wheels", "MESH_CYLINDER"),
            ("Add Windows and Lights", "MATERIAL"),
            ("Bevel the Silhouette", "MODIFIER"),
            ("Light and Render", "RENDER_STILL"),
        ),
    ),
    Challenge(
        "Cozy Room",
        "Glitchless • Advanced",
        (
            ("Build the Room Shell", "MESH_CUBE"),
            ("Model a Bed or Sofa", "EDITMODE_HLT"),
            ("Add Three Small Props", "OBJECT_DATA"),
            ("Create Materials", "MATERIAL"),
            ("Warm Light and Render", "LIGHT_DATA"),
        ),
    ),
    Challenge(
        "Modifier Gauntlet",
        "10 Modifiers • Expert",
        (
            ("Prepare Three Base Objects", "OBJECT_DATA"),
            ("Mirror and Bevel", "MODIFIER"),
            ("Array and Solidify", "MODIFIER_DATA"),
            ("Boolean, Subdivide & Three More", "ADD"),
            ("Add the Tenth and Render", "RENDER_STILL"),
        ),
    ),
    Challenge(
        "Procedural Tower",
        "Geometry Nodes • Expert",
        (
            ("Create the Tower Footprint", "MESH_CIRCLE"),
            ("Build a Floor Module", "MESH_CUBE"),
            ("Instance Ten Floors", "NODETREE"),
            ("Add Twist and Taper", "MODIFIER_DATA"),
            ("Material, Camera, Render", "VIEW_CAMERA"),
        ),
    ),
    Challenge(
        "Rainbow Material Lineup",
        "Shader% • Beginner",
        (
            ("Create Seven Objects", "DUPLICATE"),
            ("Make Red, Orange & Yellow", "COLOR"),
            ("Make Green and Blue", "MATERIAL_DATA"),
            ("Make Indigo and Violet", "NODE_MATERIAL"),
            ("Arrange and Render", "RENDER_STILL"),
        ),
    ),
    Challenge(
        "Bouncing Ball Shot",
        "Glitchless • Beginner",
        (
            ("Create Ball and Floor", "MESH_UVSPHERE"),
            ("Keyframe Three Bounces", "KEYFRAME"),
            ("Shape the Timing", "ANIM"),
            ("Add Squash and Stretch", "ORIENTATION_LOCAL"),
            ("Preview the Animation", "PLAY"),
        ),
    ),
    Challenge(
        "Studio Product Shot",
        "Any% • Advanced",
        (
            ("Choose and Model a Product", "OBJECT_DATA"),
            ("Create a Curved Backdrop", "CURVE_DATA"),
            ("Build Three-Point Lighting", "LIGHT_DATA"),
            ("Polish Materials", "MATERIAL"),
            ("Compose and Render", "VIEW_CAMERA"),
        ),
    ),
    Challenge(
        "Tiny Sculpted Creature",
        "Sculpt% • Expert",
        (
            ("Block Out the Body", "SCULPTMODE_HLT"),
            ("Sculpt the Head", "BRUSH_DATA"),
            ("Add Limbs and Silhouette", "MESH_UVSPHERE"),
            ("Paint Two Colors", "VPAINT_HLT"),
            ("Pose and Render", "RENDER_STILL"),
        ),
    ),
)


def choose_random_challenge(current_title: str = "", rng: random.Random | None = None) -> Challenge:
    """Choose a challenge, avoiding an immediate repeat when possible."""
    choices = tuple(challenge for challenge in CHALLENGES if challenge.title != current_title)
    return (rng or random).choice(choices or CHALLENGES)
