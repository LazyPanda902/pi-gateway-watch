import json
import socket
import sys
import tempfile
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from src.app import (
    CheckResult,
    check_http,
    check_tcp,
    load_config,
    main,
    pi_cpu_temp,
    pi_uptime,
    result_to_dict,
    run_checks,
)


# ---------------------------------------------------------------------------
# result_to_dict
# ---------------------------------------------------------------------------

def test_result_to_dict_fields():
    result = CheckResult("dns", "1.1.1.1:53", True, 12, "tcp reachable")
    data = result_to_dict(result)
    assert data == {
        "name": "dns",
        "target": "1.1.1.1:53",
        "ok": True,
        "latency_ms": 12,
        "detail": "tcp reachable",
    }


def test_result_to_dict_keys():
    result = CheckResult("http", "https://example.com", True, 25, "http 200")
    data = result_to_dict(result)
    assert set(data) == {"name", "target", "ok", "latency_ms", "detail"}


# ---------------------------------------------------------------------------
# check_tcp (mocked)
# ---------------------------------------------------------------------------

def test_check_tcp_success():
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("src.app.socket.create_connection", return_value=mock_conn):
        result = check_tcp("dns", "1.1.1.1", 53)

    assert result.ok is True
    assert result.name == "dns"
    assert result.target == "1.1.1.1:53"
    assert result.latency_ms >= 0
    assert "reachable" in result.detail


def test_check_tcp_failure():
    with patch(
        "src.app.socket.create_connection",
        side_effect=OSError("Connection refused"),
    ):
        result = check_tcp("broken", "10.0.0.1", 9999)

    assert result.ok is False
    assert result.name == "broken"
    assert "Connection refused" in result.detail
    assert result.latency_ms >= 0


def test_check_tcp_timeout():
    with patch(
        "src.app.socket.create_connection",
        side_effect=socket.timeout("timed out"),
    ):
        result = check_tcp("slow", "192.0.2.1", 80, timeout=0.001)

    assert result.ok is False
    assert result.latency_ms >= 0


# ---------------------------------------------------------------------------
# check_http (mocked)
# ---------------------------------------------------------------------------

def _mock_http_response(status: int):
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_check_http_success():
    with patch("src.app.urllib.request.urlopen", return_value=_mock_http_response(200)):
        result = check_http("web", "https://example.com")

    assert result.ok is True
    assert result.name == "web"
    assert result.target == "https://example.com"
    assert "200" in result.detail
    assert result.latency_ms >= 0


def test_check_http_redirect_ok():
    with patch("src.app.urllib.request.urlopen", return_value=_mock_http_response(301)):
        result = check_http("redirect", "https://example.com/old")

    assert result.ok is True
    assert "301" in result.detail


def test_check_http_server_error():
    with patch("src.app.urllib.request.urlopen", return_value=_mock_http_response(500)):
        result = check_http("broken", "https://example.com/err")

    assert result.ok is False
    assert "500" in result.detail


def test_check_http_exception():
    with patch(
        "src.app.urllib.request.urlopen",
        side_effect=urllib.error.URLError("Name or service not known"),
    ):
        result = check_http("unreachable", "https://192.0.2.1/")

    assert result.ok is False
    assert result.latency_ms >= 0


def test_check_http_http_exception():
    with patch(
        "src.app.urllib.request.urlopen",
        side_effect=Exception("unexpected"),
    ):
        with pytest.raises(Exception, match="unexpected"):
            check_http("bad", "https://example.com")


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

def test_load_config_valid():
    cfg = {
        "checks": [
            {"name": "dns", "type": "tcp", "host": "1.1.1.1", "port": 53},
            {"name": "web", "type": "http", "url": "https://example.com"},
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cfg, f)
        tmp_path = f.name

    loaded = load_config(tmp_path)
    assert len(loaded["checks"]) == 2
    assert loaded["checks"][0]["name"] == "dns"


def test_load_config_missing_checks():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"other": []}, f)
        tmp_path = f.name

    with pytest.raises(ValueError, match="checks"):
        load_config(tmp_path)


def test_load_config_tcp_missing_host():
    cfg = {"checks": [{"name": "t", "type": "tcp", "port": 80}]}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cfg, f)
        tmp_path = f.name

    with pytest.raises(ValueError, match="host"):
        load_config(tmp_path)


def test_load_config_tcp_missing_port():
    cfg = {"checks": [{"name": "t", "type": "tcp", "host": "1.1.1.1"}]}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cfg, f)
        tmp_path = f.name

    with pytest.raises(ValueError, match="port"):
        load_config(tmp_path)


def test_load_config_http_missing_url():
    cfg = {"checks": [{"name": "h", "type": "http"}]}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(cfg, f)
        tmp_path = f.name

    with pytest.raises(ValueError, match="url"):
        load_config(tmp_path)


# ---------------------------------------------------------------------------
# run_checks (mocked network)
# ---------------------------------------------------------------------------

def test_run_checks_tcp_entry():
    cfg = {"checks": [{"name": "t", "type": "tcp", "host": "1.1.1.1", "port": 53}]}

    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("src.app.socket.create_connection", return_value=mock_conn):
        results = run_checks(cfg)

    assert len(results) == 1
    assert results[0].ok is True


def test_run_checks_http_entry():
    cfg = {"checks": [{"name": "h", "type": "http", "url": "https://example.com"}]}

    with patch("src.app.urllib.request.urlopen", return_value=_mock_http_response(200)):
        results = run_checks(cfg)

    assert len(results) == 1
    assert results[0].ok is True


def test_run_checks_unknown_type():
    cfg = {"checks": [{"name": "x", "type": "icmp"}]}
    results = run_checks(cfg)
    assert results[0].ok is False
    assert "unknown check type" in results[0].detail


# ---------------------------------------------------------------------------
# Pi metric helpers
# ---------------------------------------------------------------------------

def test_pi_uptime_present(tmp_path):
    fake = tmp_path / "uptime"
    fake.write_text("12345.67 23456.78\n")

    with patch("src.app.Path") as mock_path_cls:
        mock_path_cls.return_value.read_text.return_value = "12345.67 23456.78\n"
        val = pi_uptime()

    assert val == pytest.approx(12345.67)


def test_pi_uptime_missing():
    with patch("src.app.Path") as mock_path_cls:
        mock_path_cls.return_value.read_text.side_effect = OSError("no file")
        val = pi_uptime()

    assert val is None


def test_pi_cpu_temp_present():
    with patch("src.app.Path") as mock_path_cls:
        mock_path_cls.return_value.read_text.return_value = "47500\n"
        val = pi_cpu_temp()

    assert val == pytest.approx(47.5)


def test_pi_cpu_temp_missing():
    with patch("src.app.Path") as mock_path_cls:
        mock_path_cls.return_value.read_text.side_effect = OSError("no sysfs")
        val = pi_cpu_temp()

    assert val is None


# ---------------------------------------------------------------------------
# main() — JSON output, human output, --output FILE
# ---------------------------------------------------------------------------

_FIXED_RESULTS = [
    CheckResult("dns", "1.1.1.1:53", True, 8, "tcp reachable"),
    CheckResult("web", "https://example.com", True, 91, "http 200"),
]

_FIXED_FAIL = [
    CheckResult("dns", "1.1.1.1:53", True, 8, "tcp reachable"),
    CheckResult("web", "https://example.com", False, 150, "http 500"),
]


def test_main_json_output(capsys):
    with patch("sys.argv", ["app.py", "--json"]):
        with patch("src.app._default_checks", return_value=_FIXED_RESULTS):
            rc = main()
    out, _ = capsys.readouterr()
    data = json.loads(out)
    assert rc == 0
    assert len(data["checks"]) == 2
    assert data["checks"][0]["name"] == "dns"
    assert data["checks"][0]["ok"] is True
    assert data["checks"][1]["detail"] == "http 200"


def test_main_human_output(capsys):
    with patch("sys.argv", ["app.py"]):
        with patch("src.app._default_checks", return_value=_FIXED_FAIL):
            rc = main()
    out, _ = capsys.readouterr()
    assert "OK  " in out
    assert "FAIL" in out
    assert "dns" in out
    assert "web" in out
    assert rc == 1


def test_main_output_file(tmp_path, capsys):
    out_file = tmp_path / "report.json"
    with patch("sys.argv", ["app.py", "--output", str(out_file)]):
        with patch("src.app._default_checks", return_value=_FIXED_RESULTS):
            rc = main()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["checks"][0]["name"] == "dns"
    assert rc == 0
    out, _ = capsys.readouterr()
    assert "OK  " in out


def test_main_output_file_with_json_flag(tmp_path, capsys):
    out_file = tmp_path / "report.json"
    with patch("sys.argv", ["app.py", "--json", "--output", str(out_file)]):
        with patch("src.app._default_checks", return_value=_FIXED_RESULTS):
            rc = main()
    file_data = json.loads(out_file.read_text(encoding="utf-8"))
    out, _ = capsys.readouterr()
    stdout_data = json.loads(out)
    assert file_data == stdout_data
    assert rc == 0
