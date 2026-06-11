# Usage Examples

## Built-in checks (no config required)

```bash
python src/app.py
```

```
OK   dns              1.1.1.1:53                        8ms  tcp reachable
OK   example          https://example.com              91ms  http 200
```

## JSON output

```bash
python src/app.py --json
```

```json
{
  "checks": [
    {"name": "dns", "target": "1.1.1.1:53", "ok": true, "latency_ms": 8, "detail": "tcp reachable"},
    {"name": "example", "target": "https://example.com", "ok": true, "latency_ms": 91, "detail": "http 200"}
  ]
}
```

## Multi-target config

Create a config file (`my-checks.json`) with multiple targets:

```json
{
  "checks": [
    {"name": "dns-cf",   "type": "tcp",  "host": "1.1.1.1",        "port": 53,  "timeout": 2.0},
    {"name": "dns-g",    "type": "tcp",  "host": "8.8.8.8",        "port": 53,  "timeout": 2.0},
    {"name": "ntp",      "type": "tcp",  "host": "pool.ntp.org",   "port": 123, "timeout": 2.0},
    {"name": "router",   "type": "tcp",  "host": "203.0.113.1",    "port": 80,  "timeout": 1.0},
    {"name": "web",      "type": "http", "url": "https://example.com",           "timeout": 3.0},
    {"name": "api",      "type": "http", "url": "https://httpbin.org/status/200","timeout": 5.0}
  ]
}
```

All probes run in parallel, so total time is bounded by the slowest single check:

```bash
python src/app.py --config my-checks.json
```

```
OK   dns-cf           1.1.1.1:53                        6ms  tcp reachable
OK   dns-g            8.8.8.8:53                        7ms  tcp reachable
OK   ntp              pool.ntp.org:123                 14ms  tcp reachable
OK   router           203.0.113.1:80                    3ms  tcp reachable
OK   web              https://example.com              88ms  http 200
OK   api              https://httpbin.org/status/200  210ms  http 200
```

## Pi system metrics (`--pi-info`)

On a Raspberry Pi or any Linux host, append `--pi-info` to include uptime and CPU temperature:

```bash
python src/app.py --config my-checks.json --pi-info
```

```
OK   dns-cf           1.1.1.1:53                        6ms  tcp reachable
OK   web              https://example.com              88ms  http 200
     uptime           14h 22m
     cpu_temp         51.3°C
```

JSON form:

```bash
python src/app.py --config my-checks.json --pi-info --json
```

```json
{
  "checks": [...],
  "pi": {
    "uptime_seconds": 51720.4,
    "cpu_temp_celsius": 51.3
  }
}
```

On non-Linux hosts (macOS, Windows) the `pi` fields return `null` — the tool still exits cleanly.

## Scripting with exit codes

```bash
if python src/app.py --config my-checks.json --json > /tmp/health.json; then
    echo "All checks passed"
else
    echo "One or more checks failed — see /tmp/health.json"
fi
```

Exit code `0` means every check passed; `1` means at least one failed or timed out.

## Version

```bash
python src/app.py --version
# app.py 0.1.0
```
