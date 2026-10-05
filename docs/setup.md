# Set up the dashboard

## Requirements

Use Python 3.13 or later and a network path to the Starlink terminal. The
`starlink-api-reference` submodule supplies the SpaceX `enterprise-api` protocol
file. A terminal is not required for the offline tests or screenshot capture.

## Install

1. Clone the repository and its submodule:

   ```console
   git clone --recurse-submodules https://github.com/jmorrison-juniper/starlink-dashboard.git
   cd starlink-dashboard
   ```

   For an existing clone, run `git submodule update --init`.

2. Create a virtual environment:

   ```console
   python -m venv .venv
   ```

   On Windows PowerShell, run `.venv\Scripts\Activate.ps1`. On Linux or macOS,
   run `source .venv/bin/activate`.

3. Install the runtime dependencies:

   ```console
   python -m pip install -r requirements.txt
   ```

4. Generate the protocol modules:

   ```console
   cd starlink-api-reference/device-api
   python -m grpc_tools.protoc -I . --python_out=. --pyi_out=. --grpc_python_out=. device.proto
   cd ../..
   ```

   This writes `device_pb2.py` and `device_pb2_grpc.py` into the submodule
   folder. The submodule ignores these files. Without this step, the dashboard
   starts but cannot connect to the terminal.

## Start

```console
python starlink_dashboard.py
```

If PyQt6 or the gRPC packages are missing, the app attempts to install them with
`uv`, or with `pip` if `uv` is unavailable. It restarts after installing PyQt6.
Install the dependencies before launch to avoid this automatic installation.

See [operation](operation.md) for controls and [development](development.md) for
offline checks.
