# Contributing

Thanks for your interest in BlendSplit.

## Forking is encouraged

BlendSplit is maintained as time allows, so issues and pull requests may not
receive a quick response. If you want to customize the extension or continue
developing it actively, the best approach is to fork the repository and make
it your own.

Small, focused pull requests are still welcome, but please do not rely on a
merge or a specific review timeline.

## Compatibility

BlendSplit 1.2 targets **Blender 5.2**, which includes **Python 3.13**. Users do
not need to install Python or any Python packages—the extension uses Blender's
built-in Python runtime and APIs.

Development tools and tests also target Python 3.13. Pillow is required only
for testing the bundled icon atlas, not for running BlendSplit in Blender.

## Testing changes

Install the test dependency and run the unit tests:

```bash
python3 -m pip install -r requirements-dev.txt
cd source
python3 -m unittest discover -s tests -v
```

If you have Blender 5.2 installed, also run the registration smoke test from
the repository root:

```bash
blender --background --factory-startup --python source/tests/blender_smoke.py
```

Please keep changes focused and do not commit generated ZIP files or Python
cache files.
