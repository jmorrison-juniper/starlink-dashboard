# Starlink Enterprise Dashboard

The Starlink Enterprise Dashboard is a PyQt6 desktop application. It shows the status of a Starlink Enterprise terminal.

The dashboard reads the status from the gRPC device API of the terminal. The API listens on port 9200 of the terminal address. The default address is `192.168.100.1`.

## Origin of the code

This code came from the [MistHelper](https://github.com/jmorrison-juniper/MistHelper) repository on 2026-09-25. The move kept the commit history of the dashboard files. MistHelper issue [#3403](https://github.com/jmorrison-juniper/MistHelper/issues/3403) records the move.

The commit messages and the code comments use numbers such as `#1834` and `alert 190`. These numbers identify MistHelper issues, MistHelper pull requests, and MistHelper code scanning alerts. They do not identify items in this repository.

## Requirements

1. Python 3.13 or later.
2. A network path from your computer to the Starlink terminal.
3. The protocol file of the SpaceX `enterprise-api` repository. The `starlink-api-reference` submodule supplies this file.

## Set up the dashboard

1. Clone the repository and its submodule.

   ```powershell
   git clone --recurse-submodules https://github.com/jmorrison-juniper/starlink-dashboard.git
   cd starlink-dashboard
   ```

   If you cloned the repository without the submodule, run `git submodule update --init`.

2. Create a virtual environment, and then activate it.

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   On Linux or macOS, run `source .venv/bin/activate` to activate the environment.

3. Install the dependencies.

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Generate the Python modules from the protocol file.

   ```powershell
   cd starlink-api-reference/device-api
   python -m grpc_tools.protoc -I . --python_out=. --pyi_out=. --grpc_python_out=. device.proto
   cd ../..
   ```

   This step writes `device_pb2.py` and `device_pb2_grpc.py` into the submodule folder. The submodule ignores these generated files, so the submodule stays clean. If you do not do this step, the dashboard starts, but it cannot connect to the terminal.

Caution: If PyQt6 or the gRPC packages are not installed, the dashboard installs them when it starts. It uses `uv` if `uv` is available, and it uses `pip` if `uv` is not available. After the dashboard installs PyQt6, it starts again. To prevent the automatic installation, do step 3 before you start the dashboard.

## Start the dashboard

```powershell
python starlink_dashboard.py
```

1. Type the address of the terminal in the `Starlink IP:` field.
2. Click `Connect`.
3. To read the status again at once, click `Refresh Now`.

To show the debug log in the terminal window, add the `--debug` option.

```powershell
python starlink_dashboard.py --debug
```

## GPS precision

The dashboard rounds each GPS coordinate to three decimal places. At this precision, a coordinate identifies a site to approximately 100 meters.

Warning: An exact coordinate shows the physical position of the terminal. Do not share a log or a screenshot that shows an exact coordinate.

To show the exact coordinates, set `STARLINK_DASHBOARD_EXACT_GPS` to `1`, `true`, `yes`, or `on` before you start the dashboard.

```powershell
$env:STARLINK_DASHBOARD_EXACT_GPS = "1"
python starlink_dashboard.py
```

## Run the tests

The tests read the source of the dashboard. They do not import the dashboard, so they do not need PyQt6 or gRPC.

```powershell
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

CI runs the same three checks with the shared quality gate workflow of [misthelper-devtools](https://github.com/jmorrison-juniper/misthelper-devtools). Each check is a separate job, for example `gates / Ruff (lint)`.

## License

This repository uses the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license. See [LICENSE](LICENSE).

The `starlink-api-reference` submodule is a pointer to the SpaceX `enterprise-api` repository. This repository holds no copy of that code. The SpaceX repository states no license, so read its terms before you copy its files.
