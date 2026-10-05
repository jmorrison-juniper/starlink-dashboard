# `starlink-dashboard` agent instructions

This file holds the rules that apply to `starlink-dashboard` only. The rules that apply to each
repository of this owner are in `AGENTS.md` at the repository root. Read `AGENTS.md` first. This
file adds to it, and it does not hold a copy of a rule from it. Where the two files disagree, obey
`AGENTS.md` for a writing rule, a safety rule, or a security rule.

## What this repository is

The repository holds the Starlink Enterprise Dashboard, a PyQt6 desktop application for Windows,
macOS, and Linux. The application shows the status, the alerts, and the dish alignment of one
Starlink Enterprise terminal. It reads the gRPC device API of the terminal at port `9200`, and the
default terminal address is `192.168.100.1`. The users are NOC engineers and terminal operators.
The code is Python, and one module, `starlink_dashboard.py`, holds the full application. The code
moved from the MistHelper repository on 2026-09-25, and the license is CC BY-NC-SA 4.0.

## Language and environment

Use Python 3.13 or later. The package manager is `pip`, with `requirements.txt` for the runtime
packages and `requirements-dev.txt` for the test and lint packages. The repository has no lock
file. Build a work environment in a new worktree with these commands:

```console
git submodule update --init
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
cd starlink-api-reference/device-api
python -m grpc_tools.protoc -I . --python_out=. --pyi_out=. --grpc_python_out=. device.proto
cd ../..
```

On Windows PowerShell, run `.venv\Scripts\Activate.ps1` instead of `source`.
The `starlink-api-reference` submodule is the SpaceX `enterprise-api` repository.
The `protoc` command writes `device_pb2.py`, `device_pb2.pyi`, and `device_pb2_grpc.py` into
`starlink-api-reference/device-api/`. The submodule ignores these files.
Do not commit them or copy a submodule file into this repository.
The SpaceX repository states no license.

Set `QT_QPA_PLATFORM=offscreen` before a UI test or a screenshot capture. On a minimal Ubuntu
system, install `libegl1` and `libopengl0` first. Install the STE linter in its own virtual
environment from `misthelper-devtools` with the `ste-linter` extra, at the commit that
`.github/workflows/ste-lint.yml` pins.

## Local gates

Run each command from the repository root in the activated environment.

| Gate | Command | Expected result |
| - | - | - |
| Lint | `python -m ruff check .` | `All checks passed!` |
| Format | `python -m ruff format --check .` | `<count> files already formatted` and no `Would reformat` line |
| Unit tests | `python -m pytest tests/unit` | Each test passes, with no skip |
| UI tests | `QT_QPA_PLATFORM=offscreen python -m pytest tests/ui` | Each test passes, with no skip |
| Protocol modules | The `protoc` command above, then `python -c "import device_pb2, device_pb2_grpc"` in `starlink-api-reference/device-api` | Exit code 0 and no output |
| Screenshot capture | `QT_QPA_PLATFORM=offscreen python -m tools.capture_screenshots --output /tmp/starlink-screenshots` | Three `Captured synthetic app view` lines |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md` | `PASS` for each file, with the dictionary and without it |

A skipped UI test is not a pass, because pytest skips `tests/ui` when PyQt6 or `grpc` is absent.
Ruff is the compile check, because a syntax error fails the lint gate. The repository has no type
check gate, so the `gates / mypy (types)` check reports `skipping`.

## Architecture and conventions

`starlink_dashboard.py` holds the logging setup, the dependency bootstrap, the Qt imports, and two
classes in this order. `logging.basicConfig` runs first because the bootstrap writes `INFO` and
`DEBUG` records. A test reads the module with `ast` and checks this order.
The bootstrap functions `check_and_install_uv`, `check_and_install_grpcio`, and
`check_and_install_pyqt6` install missing packages into the active interpreter.
The process restarts after a PyQt6 install. `fix_qt_plugin_path` sets `QT_PLUGIN_PATH` before
the PyQt6 import.

`MetricWidget` shows one value with a title and a unit. `StarlinkDashboard` is the main window,
and its data flow has five steps:

1. `toggle_connection` calls `connect_to_starlink`, which opens `grpc.insecure_channel` to
   `<address>:9200` with a five second ready timeout.
2. A `QTimer` calls `refresh_stats` every five seconds. Its interval is `5000` milliseconds.
3. `refresh_stats` calls `get_starlink_stats`, which calls `_fetch_diagnostics_from_terminal`
   with a `DeviceStub` and a `GetDiagnosticsRequest`.
4. `_build_starlink_stats_dict` turns the diagnostics message into the stats dictionary.
5. `update_metrics` writes the values to the widgets.

`_load_starlink_proto_modules` adds `starlink-api-reference/device-api` to `sys.path` and imports
`device_pb2` and `device_pb2_grpc`. The themes are `Light`, `Dark`, `TRON`, and `Hackers`, and
`Dark` is the default. Each theme has an `apply_<name>_theme` method.

The GPS helpers `_exact_gps_enabled` and `_format_gps_coordinate` round each coordinate to
`GPS_PRECISION_DECIMALS` decimal places, which is three. The operator sets
`STARLINK_DASHBOARD_EXACT_GPS` to `1`, `true`, `yes`, or `on` for the exact value. Each coordinate
that the module prints goes through `_format_gps_coordinate`, and a test fails on a format string
that pins a decimal count.

The test `tests/unit/test_starlink_dashboard_offline.py` compiles the data-path methods of
`StarlinkDashboard` with `ast`, without Qt or gRPC. The sets `DASHBOARD_METHODS` and
`DASHBOARD_CONSTANTS` in that test name the methods and the class constants that the harness
keeps. When you add a method or a constant to the data path, add its name to the set, or the
harness drops it. The test `tests/unit/test_starlink_dashboard_startup_and_gps.py` reads the
module with `ast` and asserts the startup order, the GPS rounding, and the CodeQL verdict comment.

`tools/capture_screenshots.py` renders the widgets offscreen with synthetic data.
`CAPTURES` names the three PNG files in `docs/screenshots/`.
`SAFE_ADDRESS` is `192.0.2.10`, the address for documentation.
`offline_guards` blocks socket connections, gRPC channels, and subprocesses.

Ruff is the linter and formatter. Its line length is 120.
Its rule sets are `E`, `F`, `W`, `I`, `UP`, `B`, and `G`.
The submodule is excluded.
References to `#1721`, `#1737`, `#1834`, or `alert 190` in comments and commit messages name
MistHelper issues or CodeQL alerts. They do not name items in this repository.

The hot files that only one agent changes at a time are `starlink_dashboard.py`, `README.md`, and
`.github/workflows/ci.yml`.

## Safety in this repository

The application only reads the terminal. It sends a `GetDiagnosticsRequest`, it changes no
terminal setting, and a theme change does not touch the terminal. The product has no destructive
operation and no confirmation word. The **Exit** button asks for a confirmation in a dialog before
the window closes.

The dependency bootstrap changes the environment. When a package is absent, it installs `uv`,
`grpcio`, `grpcio-tools`, `protobuf`, or `PyQt6` into the active interpreter, and the process
restarts after a PyQt6 install. Install the packages before you start the application, so the
bootstrap does not run. A test or a tool imports `google.protobuf`, `grpc`, and `PyQt6` before it
imports `starlink_dashboard`, so an absent package fails before the bootstrap runs.

A terminal identifier, a GPS coordinate, and a network address identify a site. Do not commit a
screenshot or a log from a live terminal. Make each documentation image with
`python -m tools.capture_screenshots`, which writes the three PNG files to `docs/screenshots/` and
marks each image `SYNTHETIC TEST DATA`. Keep the GPS rounding as the default, and leave the exact
coordinate as an opt-in for the operator.

The application stores no data file at run time, so no backup rule applies. The files that a
command writes are the three PNG files in `docs/screenshots/` and the generated protocol modules
in the submodule folder.

## Git and GitHub in this repository

The type labels are `bug`, `enhancement`, and `documentation`, and the `in-progress` label exists.
The repository has no scope label, no `auto-merge` label, no changelog, no changelog fragment
folder, and no pull request template.

The repository has three workflows.
`CI` in `.github/workflows/ci.yml` calls the shared `reusable-python-quality-gates.yml` workflow.
It runs Ruff lint, Ruff format, and pytest. It also generates the protocol modules and runs offline
UI and screenshot tests.
`STE lint` in `.github/workflows/ste-lint.yml` grades `README.md`, `AGENTS.md`, and this file.
`Stranded Branch Report` runs each Monday at 07:00 UTC.
Each pull request job finishes in less than one minute.

Branch protection requires the `gates / *` checks, `Generate the protocol modules`, and
`Offline UI and screenshot capture`. The ten gate jobs that `ci.yml` does not enable always report
`skipping`, by design, and branch protection accepts them. The `ste-lint / STE compliance` check is
not required today. The repository has no CodeQL workflow, and code scanning is not configured.

Dependabot updates the `pip` packages and the GitHub Actions pins each week, in one group for each
ecosystem. A release tag has the form `YY.MM.DD.HH.MM`, for example
`26.10.05.02.08`, with no `v` prefix. `main()` sets the application version `1.0.0` with
`setApplicationVersion`.

## Known pitfalls

- A new worktree has an empty `starlink-api-reference` folder. The `protoc` command then finds no
  `device.proto`. Run `git submodule update --init` first.

- Without generated protocol modules, the app starts but cannot connect. It shows the
  `_show_proto_files_missing_dialog` dialog. Generate the modules.

- A Qt offscreen run fails on a minimal Ubuntu system when Qt libraries are absent.
  Install `libegl1` and `libopengl0`, as `ci.yml` does.

- The root logger dropped bootstrap records below `WARNING` until `logging.basicConfig` moved
  to the top of the module (jmorrison-juniper/MistHelper#1721). Keep the logging setup first.

- The location dump printed exact GPS coordinates. CodeQL flagged the output as sensitive data
  (jmorrison-juniper/MistHelper#1737). `_format_gps_coordinate` rounds the values.
  Keep the verdict markers in `_dump_diagnostics_location`.

- `pytest` skips `tests/ui` when PyQt6 or `grpc` is absent. A skip is not a pass.
  Install `requirements.txt` before you trust a UI test result.

## Key files

| File | Purpose |
| - | - |
| `starlink_dashboard.py` | The full application: the bootstrap, the widgets, the gRPC data path, and the themes |
| `tools/capture_screenshots.py` | The offscreen capture of the three synthetic views, with network guards |
| `tests/unit/test_starlink_dashboard_offline.py` | The `ast` harness that runs the data-path methods with a mocked terminal |
| `tests/unit/test_starlink_dashboard_startup_and_gps.py` | The startup order, GPS rounding, and CodeQL verdict tests |
| `tests/unit/test_documentation.py` | The README section names, the local links, and the three captures |
| `tests/ui/test_screenshots.py` | The real widget states and the capture safety with PyQt6 offscreen |
| `docs/setup.md` | The install steps for an operator |
| `docs/operation.md` | The controls, the troubleshooting steps, and the GPS privacy opt-in |
| `docs/development.md` | The quality checks and the safe screenshot capture |
| `docs/project.md` | The origin, the license, and the submodule terms |
| `starlink-api-reference/` | The SpaceX `enterprise-api` submodule with `device-api/device.proto` |
| `requirements.txt` | The runtime package floors |
| `requirements-dev.txt` | The test and lint package floors |
| `pyproject.toml` | The Ruff and pytest settings |
| `.github/workflows/ci.yml` | The quality gates, the protocol module job, and the UI and capture job |

## External resources

- [SpaceX enterprise-api](https://github.com/SpaceExplorationTechnologies/enterprise-api): the
  `device.proto` source and the gRPC device API.
- [PyQt6 reference](https://www.riverbankcomputing.com/static/Docs/PyQt6/): the widget and the
  signal documentation.
- [gRPC Python](https://grpc.io/docs/languages/python/): the channel, the stub, and the
  `grpc_tools.protoc` documentation.
- [misthelper-devtools](https://github.com/jmorrison-juniper/misthelper-devtools): the shared
  workflows and the STE linter.
  It also holds the STE writing guide and the canonical `AGENTS.md`.
- [MistHelper](https://github.com/jmorrison-juniper/MistHelper): the origin of the code, and
  issue 3403 there records the move.
