"""Exercise real widgets and capture safety without any Starlink terminal."""

import socket
import subprocess

import pytest

from tools.capture_screenshots import CAPTURES, SAFE_ADDRESS, capture, configure_view, load_ui, offline_guards

pytest.importorskip("PyQt6")
grpc = pytest.importorskip("grpc")


@pytest.fixture(scope="module")
def ui():
    with offline_guards():
        application_type, dashboard_type = load_ui()
        app = application_type.instance() or application_type([])
        yield app, dashboard_type


@pytest.mark.parametrize("filename", CAPTURES)
def test_real_widget_states(ui, filename):
    _, dashboard_type = ui
    with offline_guards():
        window = dashboard_type()
        try:
            configure_view(window, filename)
            assert window.ip_input.text() == SAFE_ADDRESS
            assert "SYNTHETIC TEST DATA" in window.status_bar.currentMessage()
            assert not window.timer.isActive()
            if filename == CAPTURES[0]:
                assert not window.connected
                assert not window.refresh_button.isEnabled()
                assert window.connection_status.value_label.text() == "--"
                assert window.current_theme == "Dark"
            else:
                assert window.connected
                assert window.client_status_label.text() == "Client: CONNECTED"
                assert window.connect_button.text() == "Disconnect"
                assert window.refresh_button.isEnabled()
                assert not window.ip_input.isEnabled()
                assert window.connection_status.value_label.text() == "ONLINE"
                assert window.terminal_id.value_label.text() == "SYNTHETIC-TERMINAL"
                assert window.service_status.value_label.text() == "ACTIVE"
                assert "Location:" not in window.status_text.text()
                if filename == CAPTURES[1]:
                    assert window.current_theme == "Light"
                    assert window.obstruction_widget.value_label.text() == "CLEAR"
                else:
                    assert window.current_theme == "TRON"
                    assert window.obstruction_widget.value_label.text() == "OBSTRUCTED"
                    assert "#EF5350" in window.azimuth_current.value_label.styleSheet()
                window.connect_button.click()
                assert not window.connected
                assert not window.refresh_button.isEnabled()
                assert window.ip_input.isEnabled()
        finally:
            window.close()


def test_external_io_is_blocked():
    with offline_guards(), socket.socket() as client:
        for connect in (client.connect, client.connect_ex, socket.create_connection):
            with pytest.raises(RuntimeError, match="forbids network"):
                connect((SAFE_ADDRESS, 9200))
        for channel in (grpc.insecure_channel, grpc.secure_channel):
            with pytest.raises(RuntimeError, match="forbids network"):
                channel(f"{SAFE_ADDRESS}:9200")
        for spawn in (subprocess.run, subprocess.Popen):
            with pytest.raises(RuntimeError, match="subprocesses"):
                spawn(["must-not-execute"])


def test_capture_writes_real_pngs(ui, tmp_path):
    from PyQt6.QtGui import QImage

    paths = capture(tmp_path)
    assert [path.name for path in paths] == list(CAPTURES)
    for path in paths:
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        image = QImage(str(path))
        assert not image.isNull()
        assert image.width() >= 1400
        assert image.height() >= 1100


def test_capture_write_failure_is_explicit(ui, tmp_path, monkeypatch):
    from PyQt6.QtGui import QPixmap

    monkeypatch.setattr(QPixmap, "save", lambda *args: False)
    with pytest.raises(RuntimeError, match="Failed to save dashboard capture"):
        capture(tmp_path)
