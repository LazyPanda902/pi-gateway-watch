# Pi Gateway Watch

A lightweight Python utility that checks Raspberry Pi gateway health by running
configurable TCP and HTTP probes and optionally reporting Pi system metrics
such as uptime and CPU temperature.

## Features

- TCP reachability checks with latency measurement
- HTTP endpoint health checks (2xx–3xx = OK)
- Parallel probe execution via `ThreadPoolExecutor` for fast multi-target runs
- JSON config file for defining checks without editing code
- Raspberry Pi system metrics: uptime and CPU temperature
- Human-readable or JSON output
- `--output FILE` to save the JSON report to a file for logging or downstream processing
- Predictable exit codes (0 = all OK, 1 = any failure) for scripting

## Requirements

- No external runtime dependencies (stdlib only)
- `pytest` for running the test suite

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the built-in sample checks:

```bash
python src/app.py
python src/app.py --json
```

Run checks from a config file:

```bash
python src/app.py --config config.example.json
python src/app.py --config config.example.json --json
```

Include Pi system metrics:

```bash
python src/app.py --pi-info
python src/app.py --config config.example.json --pi-info --json
```

Save results to a JSON file:

```bash
python src/app.py --output report.json
python src/app.py --config config.example.json --json --output report.json
```

Print the version:

```bash
python src/app.py --version
```

### Exit codes

| Code | Meaning                                  |
|------|------------------------------------------|
| `0`  | All checks passed                        |
| `1`  | One or more checks failed or timed out   |

This makes the tool shell-script and cron friendly — wrap it in `if python src/app.py; then ...` or check `$?` directly.

### Example output

```
OK   dns              1.1.1.1:53                        8ms  tcp reachable
OK   web              https://example.com              91ms  http 200
     uptime           3h 42m
     cpu_temp         47.5°C
```

### Example JSON output

```json
{
  "checks": [
    {"name": "dns", "target": "1.1.1.1:53", "ok": true, "latency_ms": 8, "detail": "tcp reachable"},
    {"name": "web", "target": "https://example.com", "ok": true, "latency_ms": 91, "detail": "http 200"}
  ],
  "pi": {
    "uptime_seconds": 13320.4,
    "cpu_temp_celsius": 47.5
  }
}
```

## Config format

`config.example.json` shows the full schema:

```json
{
  "checks": [
    {"name": "dns",  "type": "tcp",  "host": "1.1.1.1",     "port": 53,  "timeout": 2.0},
    {"name": "web",  "type": "http", "url": "https://example.com",        "timeout": 3.0},
    {"name": "ntp",  "type": "tcp",  "host": "pool.ntp.org", "port": 123, "timeout": 2.0}
  ]
}
```

Fields:

| Field     | Required for     | Description                        |
|-----------|------------------|------------------------------------|
| `name`    | all              | Label shown in output              |
| `type`    | all              | `"tcp"` or `"http"`                |
| `host`    | tcp              | Hostname or IP                     |
| `port`    | tcp              | Port number                        |
| `url`     | http             | Full URL                           |
| `timeout` | all (optional)   | Timeout in seconds (default: 2–3)  |

## Testing

```bash
pytest tests/ -v
```

All tests use mocks — no real network calls are made.

## Pi metrics

| Metric              | Source                                       |
|---------------------|----------------------------------------------|
| `uptime_seconds`    | `/proc/uptime`                               |
| `cpu_temp_celsius`  | `/sys/class/thermal/thermal_zone0/temp`      |

Both values return `null` gracefully when run outside a Linux environment.

## Security

- Use only public or test targets in config files committed to version control.
- Do not commit real gateway IPs, private hostnames, API tokens, or `.env` files.
- See [SECURITY.md](SECURITY.md) and [PRIVACY.md](PRIVACY.md) for details.

## License

MIT
