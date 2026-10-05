# Development and safe screenshots

## Quality checks

With Python 3.13 or later in an activated virtual environment:

```console
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

The unit tests use a Qt-free harness. They execute the app's diagnostics and
connection methods with mocked gRPC endpoints and protocol modules. They never
connect to a terminal.

The UI tests require the runtime dependencies too:

```console
python -m pip install -r requirements.txt
QT_QPA_PLATFORM=offscreen python -m pytest tests/ui
```

On PowerShell, set `$env:QT_QPA_PLATFORM = "offscreen"` before the test command.
Without PyQt6 or gRPC, the UI tests are skipped; this does not verify captures.
CI installs both requirements files in a separate UI job and runs the capture
command as well as the UI tests. The shared
[misthelper-devtools](https://github.com/jmorrison-juniper/misthelper-devtools)
workflow runs lint, format, and unit tests. Another job generates and imports
the protocol modules.

## Capture genuine app images

Run from the repository root with runtime dependencies installed:

```console
python -m tools.capture_screenshots
```

The tool renders the actual `StarlinkDashboard` widgets with Qt's offscreen
platform and saves PNG files in `docs/screenshots/`. It does not draw a replica
or use generated artwork. The ready screen, active-service Light screen, and
obstruction-alert TRON screen show three operator views of the same app.

The capture harness replaces connection and statistics methods with synthetic
fixtures. It uses the documentation-only address `192.0.2.10`, a visibly
synthetic terminal ID, synthetic firmware and alignment values, and no GPS
coordinates or credentials. Each image is marked **SYNTHETIC TEST DATA** in the
app's status bar and title. Timer-driven refresh is stopped for capture.

During import and rendering, network connection calls and subprocess execution
raise errors. Missing runtime dependencies fail before importing the app, so
the capture command cannot trigger the app's dependency installer. PNG write
errors also fail the command. Do not substitute images from a live terminal.

The captures committed here were rendered on macOS with Python 3.13 and
PyQt6 6.11. Offscreen rendering on other platforms can change fonts and pixel
dimensions. Tests verify real widget states, safety guards, and valid image
output rather than byte-for-byte pixel snapshots.

For a temporary output directory:

```console
python -m tools.capture_screenshots --output /tmp/starlink-screenshots
```
