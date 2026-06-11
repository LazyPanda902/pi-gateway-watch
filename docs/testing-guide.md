# Testing Guide

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the suite

```bash
pytest tests/ -v
```

## How the tests work

All network calls are intercepted with `unittest.mock.patch` — no real TCP connections or HTTP requests are made. This keeps the suite fast, deterministic, and safe to run in any environment including CI.

Specifically:

- **TCP checks** — `socket.create_connection` is patched to return a mock context-manager (success path) or raise `OSError`/`socket.timeout` (failure paths).
- **HTTP checks** — `urllib.request.urlopen` is patched to return a mock response object whose `.status` attribute is set to the desired HTTP status code.
- **Pi metric helpers** — `pathlib.Path` is patched so `read_text()` returns a controlled string or raises `OSError`, without touching `/proc/uptime` or the thermal sysfs node.
- **Config loading** — uses real `tempfile.NamedTemporaryFile` files so `json.load` runs against genuine JSON content.

## Test categories

| File | What it covers |
|------|----------------|
| `tests/test_app.py` | `CheckResult` serialisation, TCP/HTTP probe logic, config loading, `run_checks` dispatch, Pi metric helpers |

## CI

GitHub Actions runs the full suite on every push and pull request across Python 3.11, 3.12, and 3.13. See `.github/workflows/ci.yml`.
