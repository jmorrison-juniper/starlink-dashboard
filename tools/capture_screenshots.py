"""Render the real dashboard with synthetic data and fail-closed network guards."""

import argparse
import os
import socket
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

SAFE_ADDRESS = "192.0.2.10"
CAPTURES = ("disconnected-dark.png", "active-light.png", "alert-tron.png")
ACTIVE_STATS = {
    "connected": True,
    "service_status": "ACTIVE",
    "hardware_test": "PASSED",
    "obstruction_status": "CLEAR",
    "terminal_id": "SYNTHETIC-TERMINAL",
    "software_version": "demo-firmware-1.0",
    "hardware_version": "DEMO-HARDWARE",
    "utc_offset_hours": 0,
    "azimuth_current": 180.0,
    "elevation_current": 65.0,
    "azimuth_target": 182.0,
    "elevation_target": 66.0,
    "status_message": "Synthetic terminal: all checks passed.\nNo live terminal data or GPS coordinates.",
}
ALERT_STATS = {
    **ACTIVE_STATS,
    "obstruction_status": "OBSTRUCTED",
    "azimuth_current": 170.0,
    "status_message": "Synthetic alert: obstruction detected.\nDish azimuth differs from target by 12 degrees.",
}


def deny_external_io(*args, **kwargs):
    raise RuntimeError("Screenshot capture forbids network connections and subprocesses")


@contextmanager
def offline_guards() -> Iterator[None]:
    import grpc

    with (
        patch.object(socket.socket, "connect", deny_external_io),
        patch.object(socket.socket, "connect_ex", deny_external_io),
        patch.object(socket, "create_connection", deny_external_io),
        patch.object(grpc, "insecure_channel", deny_external_io),
        patch.object(grpc, "secure_channel", deny_external_io),
        patch.object(subprocess, "run", deny_external_io),
        patch.object(subprocess, "Popen", deny_external_io),
    ):
        yield


def load_ui():
    # Require dependencies before importing the app's automatic installer.
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    import google.protobuf  # noqa: F401
    import grpc  # noqa: F401
    from PyQt6.QtWidgets import QApplication

    import starlink_dashboard

    return QApplication, starlink_dashboard.StarlinkDashboard


def configure_view(window, filename: str) -> None:
    if filename not in CAPTURES:
        raise ValueError(f"Unknown screenshot view: {filename}")
    window.ip_input.setText(SAFE_ADDRESS)
    window.setWindowTitle("Starlink Enterprise Dashboard - SYNTHETIC TEST DATA")
    if filename != CAPTURES[0]:
        stats = ACTIVE_STATS if filename == CAPTURES[1] else ALERT_STATS
        with (
            patch.object(window, "connect_to_starlink", return_value=True),
            patch.object(window, "get_starlink_stats", return_value=dict(stats)),
        ):
            window.connect_button.click()
        window.timer.stop()
        window.theme_selector.setCurrentText("Light" if filename == CAPTURES[1] else "TRON")
        window.timestamp_label.setText("Last Updated: Synthetic fixture")
    window.status_bar.showMessage("SYNTHETIC TEST DATA - offline capture; no live terminal")


def capture(output: Path) -> list[Path]:
    with offline_guards():
        application_type, dashboard_type = load_ui()
        app = application_type.instance() or application_type([])
        output.mkdir(parents=True, exist_ok=True)
        paths = []
        for filename in CAPTURES:
            window = dashboard_type()
            try:
                configure_view(window, filename)
                window.resize(1400, 1100)
                window.show()
                app.processEvents()
                path = output / filename
                image = window.grab()
                if image.isNull() or not image.save(str(path), "PNG"):
                    raise RuntimeError(f"Failed to save dashboard capture: {path}")
                paths.append(path)
            finally:
                window.timer.stop()
                window.close()
        return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "docs" / "screenshots")
    args = parser.parse_args()
    for path in capture(args.output):
        print(f"Captured synthetic app view: {path}")


if __name__ == "__main__":
    main()
