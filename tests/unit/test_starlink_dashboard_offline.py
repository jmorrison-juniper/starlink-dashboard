"""Offline integration tests for the dashboard's Starlink gRPC path."""

import ast
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "starlink_dashboard.py"
GPS_HELPERS = {"_exact_gps_enabled", "_format_gps_coordinate"}
DASHBOARD_METHODS = {
    "_build_starlink_stats_dict",
    "_collect_status_parts",
    "_compute_alignment",
    "_compute_hardware_test",
    "_compute_is_operational",
    "_compute_obstruction_status",
    "_compute_service_status",
    "_compute_short_terminal_id",
    "_compute_utc_offset_hours",
    "_describe_diagnostics",
    "_dump_diagnostics_alerts",
    "_dump_diagnostics_alignment",
    "_dump_diagnostics_debug",
    "_dump_diagnostics_location",
    "_dump_diagnostics_main_fields",
    "_dump_diagnostics_sub_messages",
    "_fetch_diagnostics_from_terminal",
    "_load_starlink_proto_modules",
    "_safe_diag_field",
    "_status_part_alerts",
    "_status_part_disablement",
    "_status_part_location",
    "_status_part_self_test",
    "_status_part_stowed",
    "_status_part_terminal_id",
    "connect_to_starlink",
    "format_status_message",
    "get_starlink_stats",
}
DASHBOARD_CONSTANTS = {
    "_DEFAULT_STARLINK_STATS",
    "_DISABLEMENT_CODE_MESSAGES",
    "_HARDWARE_TEST_RESULTS",
    "_SERVICE_STATUS_CODES",
    "_STATUS_ALERT_FIELDS",
}


def load_dashboard_class():
    """Compile the real data-path methods without importing desktop or network dependencies."""
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"), filename=str(MODULE_PATH))
    module_body = []
    dashboard_node = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "StarlinkDashboard"
    )
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name)
            and target.id in {"GPS_PRECISION_DECIMALS", "GPS_EXACT_ENV_VAR", "GPS_EXACT_OPT_IN_VALUES"}
            for target in node.targets
        ):
            module_body.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in GPS_HELPERS:
            module_body.append(node)

    dashboard_node.bases = []
    dashboard_node.keywords = []
    dashboard_node.body = [
        node
        for node in dashboard_node.body
        if (isinstance(node, ast.FunctionDef) and node.name in DASHBOARD_METHODS)
        or (
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and any(
                isinstance(target, ast.Name) and target.id in DASHBOARD_CONSTANTS
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            )
        )
    ]
    module_body.append(dashboard_node)
    namespace: dict[str, Any] = {
        "__file__": str(MODULE_PATH),
        "__name__": "starlink_dashboard_offline_harness",
        "datetime": datetime,
        "UTC": UTC,
        "Any": Any,
        "logging": logging,
        "logger": logging.getLogger("starlink_dashboard_offline_harness"),
        "os": os,
    }
    exec(compile(ast.Module(body=module_body, type_ignores=[]), str(MODULE_PATH), "exec"), namespace)
    return namespace["StarlinkDashboard"]


@pytest.fixture
def dashboard():
    """Create a lightweight instance of the real dashboard data-path methods."""
    dashboard_type = load_dashboard_class()
    instance = dashboard_type()
    instance.channel = None
    instance.starlink_ip = "192.0.2.10"
    instance.connection_start_time = None
    instance.dish_connected = False
    return instance


class FakeRequest:
    """Minimal protobuf request shape consumed by the dashboard."""

    def __init__(self) -> None:
        self.get_diagnostics = FakeRequestPayload()


class FakeRequestPayload:
    """Nested request field with protobuf's CopyFrom method."""

    def __init__(self) -> None:
        self.copied_request = None

    def CopyFrom(self, request: Any) -> None:
        self.copied_request = request


class FakeDiagnosticsRequest:
    """Marker object for the nested protobuf diagnostics request."""


class FakeDeviceStub:
    """Mock terminal endpoint that records requests and returns a configured response."""

    def __init__(self, channel: object, response: object = None, error: Exception | None = None) -> None:
        self.channel = channel
        self.response = response
        self.error = error
        self.requests: list[tuple[FakeRequest, float]] = []

    def Handle(self, request: FakeRequest, timeout: float):
        self.requests.append((request, timeout))
        if self.error is not None:
            raise self.error
        return self.response


def install_fake_protocol(
    monkeypatch: pytest.MonkeyPatch, response: object = None, error: Exception | None = None
) -> FakeDeviceStub:
    """Make the application's lazy protocol imports resolve to an offline stub."""
    pb2 = ModuleType("device_pb2")
    pb2.Request = FakeRequest
    pb2.GetDiagnosticsRequest = FakeDiagnosticsRequest

    pb2_grpc = ModuleType("device_pb2_grpc")
    stub = FakeDeviceStub(channel=object(), response=response, error=error)
    pb2_grpc.DeviceStub = lambda channel: stub

    monkeypatch.setitem(sys.modules, "device_pb2", pb2)
    monkeypatch.setitem(sys.modules, "device_pb2_grpc", pb2_grpc)
    return stub


class FakeResponse:
    """Response with the protobuf HasField behavior used by the dashboard."""

    def __init__(self, diagnostics: object | None) -> None:
        self.dish_get_diagnostics = diagnostics

    def HasField(self, name: str) -> bool:
        assert name == "dish_get_diagnostics"
        return self.dish_get_diagnostics is not None


def populated_diagnostics() -> SimpleNamespace:
    """Return representative terminal diagnostics without any real-device data."""
    return SimpleNamespace(
        id="12345678terminal12345678",
        software_version="2026.10.01",
        hardware_version="rev-test",
        utc_offset_s=-18000,
        hardware_self_test=1,
        disablement_code=1,
        stowed=False,
        alerts=SimpleNamespace(
            obstructed=True,
            dish_thermal_shutdown=False,
            motors_stuck=False,
            dish_thermal_throttle=False,
            mast_not_near_vertical=False,
            dish_is_heating=False,
            slow_ethernet_speeds=False,
        ),
        alignment_stats=SimpleNamespace(
            boresight_azimuth_deg=10.5,
            boresight_elevation_deg=20.5,
            desired_boresight_azimuth_deg=11.5,
            desired_boresight_elevation_deg=21.5,
        ),
        location=SimpleNamespace(enabled=True, latitude=37.7749295, longitude=-122.4194155),
    )


def test_diagnostics_request_maps_mocked_terminal_response(dashboard, monkeypatch: pytest.MonkeyPatch) -> None:
    """A mocked gRPC response traverses request, parsing, status, and display mapping."""
    response = FakeResponse(populated_diagnostics())
    stub = install_fake_protocol(monkeypatch, response=response)
    dashboard.channel = object()

    stats = dashboard.get_starlink_stats()

    assert len(stub.requests) == 1
    request, timeout = stub.requests[0]
    assert isinstance(request, FakeRequest)
    assert isinstance(request.get_diagnostics.copied_request, FakeDiagnosticsRequest)
    assert timeout == 10
    assert stats == {
        "connected": True,
        "service_status": "ACTIVE",
        "hardware_test": "PASSED",
        "obstruction_status": "OBSTRUCTED",
        "terminal_id": "12345678...12345678",
        "software_version": "2026.10.01",
        "hardware_version": "rev-test",
        "utc_offset_hours": -5.0,
        "azimuth_current": 10.5,
        "elevation_current": 20.5,
        "azimuth_target": 11.5,
        "elevation_target": 21.5,
        "status_message": "Terminal ID: 12345678terminal12345678\n"
        "Self Test: PASSED\n"
        "Service: ACTIVE\n"
        "Alerts: Obstructed\n"
        "Location: 37.775, -122.419",
    }


@pytest.mark.parametrize(
    ("response", "error"),
    [
        (FakeResponse(None), None),
        (None, RuntimeError("mock terminal unavailable")),
    ],
)
def test_missing_or_failed_terminal_diagnostics_return_fresh_defaults(
    dashboard, monkeypatch: pytest.MonkeyPatch, response: object, error: Exception | None
) -> None:
    """Missing fields and RPC errors return independent copies of safe defaults."""
    install_fake_protocol(monkeypatch, response=response, error=error)
    dashboard.channel = object()

    first = dashboard.get_starlink_stats()
    first["connected"] = True
    second = dashboard.get_starlink_stats()

    assert first["connected"] is True
    assert second == dashboard._DEFAULT_STARLINK_STATS
    assert second is not dashboard._DEFAULT_STARLINK_STATS


@pytest.mark.parametrize("timeout", [False, True])
def test_connection_uses_mocked_grpc_and_handles_timeout(
    dashboard, monkeypatch: pytest.MonkeyPatch, timeout: bool
) -> None:
    """Connection setup targets the configured address and fails cleanly on timeout."""

    class FutureTimeoutError(Exception):
        pass

    channel = object()
    calls: list[tuple[str, object]] = []

    def insecure_channel(target: str, options: list[tuple[str, int]]) -> object:
        calls.append((target, options))
        return channel

    class ReadyFuture:
        def result(self, timeout: int) -> None:
            assert timeout == 5
            if timeout_requested:
                raise FutureTimeoutError

    timeout_requested = timeout
    fake_grpc = ModuleType("grpc")
    fake_grpc.insecure_channel = insecure_channel
    fake_grpc.channel_ready_future = lambda candidate: ReadyFuture()
    fake_grpc.FutureTimeoutError = FutureTimeoutError
    monkeypatch.setitem(sys.modules, "grpc", fake_grpc)
    dashboard.starlink_ip = "192.0.2.10"

    connected = dashboard.connect_to_starlink()

    assert calls == [("192.0.2.10:9200", [("grpc.max_receive_message_length", 10 * 1024 * 1024)])]
    assert connected is not timeout
    if connected:
        assert dashboard.channel is channel
        assert dashboard.connection_start_time is not None
        assert dashboard.connection_start_time.utcoffset().total_seconds() == 0
