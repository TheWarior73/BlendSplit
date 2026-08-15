# BlendSplit 1.3.0

BlendSplit is a lightweight, LiveSplit-inspired speedrun timer built directly
into Blender's 3D Viewport. Version 1.3 targets Blender 5.2 and is authored by
Polyfjord.

## What's new in 1.3

- Start and finish a simple timer with PB comparisons without configuring splits first
- Edit splits, save profiles, and import or export setups after finishing a run
- Apply split icons immediately without an extra confirmation click
- Start with only the Run panel expanded; Blender remembers later panel choices

## Features

- Accurate monotonic timer independent of viewport frame rate
- Start, split, pause, resume, undo, skip, and reset controls
- Editable run title, category, and split names
- Persistent local profile library with a compact profile selector
- Automatic profile restoration after creating a new Blender file
- Ten built-in random speedrun challenges with five meaningful splits each
- Curated Blender split icons shared by the N-panel and viewport overlay
- JSON import/export for reusable run-list setups
- Personal-best cumulative times and best individual segments
- Automatic attempt counter with an optional manual starting value
- High-contrast 3D Viewport overlay with four anchors
- Adjustable overlay scale, offsets, opacity, precision, and visible rows
- Adjustable overlay width and optional attempts/PB information
- N-panel controls under **3D Viewport > Sidebar > Speedrun**
- Blender-native, editable add-on keymap entries
- Symmetrical cleanup of timers, handlers, draw callbacks, and keymaps

Run definitions and recorded times are saved with the `.blend` file. Optional
Blender icons appear consistently in the N-panel and viewport overlay. Active
timer state is session-only and resets when another file is loaded.

## Persistent profiles

Click **Create Profile** to link the current run to BlendSplit's local profile
library. Once linked, its title, category, splits, icons, attempts, PBs, and
best segments save automatically outside the `.blend` file. The most recently
used profile is restored after `Ctrl N` by default.

Use the profile menu to switch runs. The save button writes immediately, the
duplicate button creates a separate copy, and the trash button deletes only
the persistent profile while leaving the current scene data intact. Automatic
restoration can be disabled in the extension preferences.

Profiles are stored as versioned JSON in Blender's user configuration folder.
Writes are atomic and one valid backup is retained.

## Install

1. Build the extension ZIP or download `blendsplit-1.3.0.zip`.
2. In Blender 5.2, open **Edit > Preferences > Extensions**.
3. Open the menu and choose **Install from Disk**.
4. Select the ZIP and enable **BlendSplit**.
5. Open a 3D Viewport, press `N`, and select the **Speedrun** tab.

## Default hotkeys

| Action | Shortcut |
|---|---|
| Start / Split | `Ctrl Shift Alt 1` |
| Pause / Resume | `Ctrl Shift Alt 2` |
| Undo Split | `Ctrl Shift Alt 3` |
| Skip Split | `Ctrl Shift Alt 4` |
| Reset | `Ctrl Shift Alt 5` |
| Toggle Overlay | `Ctrl Shift Alt 6` |

Hotkeys can be changed in Blender's Keymap preferences.

## Development

Run core tests without Blender:

```bash
python -m unittest discover -s tests -v
```

Validate registration in Blender:

```bash
blender --background --factory-startup --python tests/blender_smoke.py
```

Build the distributable:

```bash
blender --command extension build --source-dir .
```

## License

GPL-3.0-or-later.
