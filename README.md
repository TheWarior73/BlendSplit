# BlendSplit

BlendSplit is a LiveSplit-inspired speedrun timer that lives right inside
Blender's 3D Viewport. It keeps your timer, splits, personal bests, and run
profiles close by, so you can focus on the speedrun instead of juggling a
second app.

BlendSplit 1.2 is made for Blender 5.2.

## What it can do

- Start, split, pause, resume, undo, skip, and reset a run
- Show a clear, customizable timer overlay in the 3D Viewport
- Save personal bests, best segments, and attempt counts
- Keep a local library of reusable run profiles
- Import and export run lists as JSON
- Pick from ten built-in random Blender speedrun challenges
- Use Blender icons for splits in both the sidebar and overlay
- Customize all shortcuts through Blender's normal Keymap preferences

Run definitions and recorded times can be saved in a `.blend` file. Persistent
profiles are stored separately in Blender's user configuration folder, with an
automatic backup. The currently running timer is session-only and resets when
another file is loaded.

## Install

1. Download the latest `blendsplit-*.zip` from
   [GitHub Releases](https://github.com/polyfjord/BlendSplit/releases/latest).
2. In Blender, open **Edit > Preferences > Extensions**.
3. Open the menu in the top-right and choose **Install from Disk**.
4. Select the ZIP file and enable **BlendSplit**.
5. Open a 3D Viewport, press `N`, and choose the **Speedrun** tab.

Do not unzip the download before installing it.

## Default shortcuts

| Action | Shortcut |
|---|---|
| Start / Split | `Ctrl Shift Alt 1` |
| Pause / Resume | `Ctrl Shift Alt 2` |
| Undo Split | `Ctrl Shift Alt 3` |
| Skip Split | `Ctrl Shift Alt 4` |
| Reset | `Ctrl Shift Alt 5` |
| Toggle Overlay | `Ctrl Shift Alt 6` |

## Working on BlendSplit

The extension source is in [`source/`](source/). To run the tests without
opening Blender:

```bash
cd source
python3 -m unittest discover -s tests -v
```

To check registration from a Blender installation:

```bash
blender --background --factory-startup --python source/tests/blender_smoke.py
```

To create an installable ZIP in `dist/`:

```bash
python3 tools/build_extension.py
```

Pushing a tag such as `v1.2.0` runs the tests, builds the ZIP, and publishes it
as a GitHub Release automatically.

## License

BlendSplit is free software under the
[GNU General Public License v3.0 or later](LICENSE). The bundled Blender icon
artwork has its own attribution details in
[`source/assets/icons/NOTICE.md`](source/assets/icons/NOTICE.md).
