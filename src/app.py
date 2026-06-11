import argparse
import http.client
import json
import socket
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

__version__ = "0.1.0"


@dataclass
class CheckResult:
    name: str
    target: str
    ok: bool
    latency_ms: int
    detail: str


def check_tcp(name: str, host: str, port: int, timeout: float = 2.0) -> CheckResult:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            latency = int((time.perf_counter() - start) * 1000)
            return CheckResult(name, f"{host}:{port}", True, latency, "tcp reachable")
    except OSError as exc:
        latency = int((time.perf_counter() - start) * 1000)
        return CheckResult(name, f"{host}:{port}", False, latency, str(exc))


def check_http(name: str, url: str, timeout: float = 3.0) -> CheckResult:
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            latency = int((time.perf_counter() - start) * 1000)
            ok = 200 <= response.status < 400
            return CheckResult(name, url, ok, latency, f"http {response.status}")
    except (urllib.error.URLError, http.client.HTTPException) as exc:
        latency = int((time.perf_counter() - start) * 1000)
        return CheckResult(name, url, False, latency, str(exc))


def load_config(path: str) -> dict:
    """Load check definitions from a JSON config file."""
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
    if "checks" not in config or not isinstance(config["checks"], list):
        raise ValueError("Config must have a 'checks' list")
    for i, entry in enumerate(config["checks"]):
        kind = entry.get("type")
        label = entry.get("name", f"entry[{i}]")
        if kind == "tcp":
            if not entry.get("host"):
                raise ValueError(f"TCP check {label!r} is missing 'host'")
            if entry.get("port") is None:
                raise ValueError(f"TCP check {label!r} is missing 'port'")
        elif kind == "http":
            if not entry.get("url"):
                raise ValueError(f"HTTP check {label!r} is missing 'url'")
    return config


def _run_entry(entry: dict) -> CheckResult:
    kind = entry.get("type")
    name = entry.get("name", "unnamed")
    if kind == "tcp":
        return check_tcp(name, entry["host"], int(entry["port"]), float(entry.get("timeout", 2.0)))
    if kind == "http":
        return check_http(name, entry["url"], float(entry.get("timeout", 3.0)))
    return CheckResult(name, str(entry), False, 0, f"unknown check type: {kind!r}")


def run_checks(config: dict) -> list[CheckResult]:
    """Execute checks in parallel using a thread pool."""
    entries = config["checks"]
    results: list[CheckResult] = [None] * len(entries)  # type: ignore[list-item]
    with ThreadPoolExecutor(max_workers=min(len(entries), 16)) as pool:
        futures = {pool.submit(_run_entry, e): i for i, e in enumerate(entries)}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results


def pi_uptime() -> Optional[float]:
    """Return system uptime in seconds from /proc/uptime, or None if unavailable."""
    try:
        text = Path("/proc/uptime").read_text()
        return float(text.split()[0])
    except (OSError, ValueError):
        return None


def pi_cpu_temp() -> Optional[float]:
    """Return CPU temperature in Celsius from the thermal sysfs node, or None if unavailable."""
    thermal_path = "/sys/class/thermal/thermal_zone0/temp"
    try:
        raw = Path(thermal_path).read_text().strip()
        return int(raw) / 1000.0
    except (OSError, ValueError):
        return None


def result_to_dict(result: CheckResult) -> dict:
    return {
        "name": result.name,
        "target": result.target,
        "ok": result.ok,
        "latency_ms": result.latency_ms,
        "detail": result.detail,
    }


def _default_checks() -> list[CheckResult]:
    return [
        check_tcp("dns", "1.1.1.1", 53),
        check_http("example", "https://example.com"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run gateway health checks.")
    parser.add_argument("--config", metavar="FILE", help="Path to JSON config file")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--output", metavar="FILE", help="Write JSON report to FILE")
    parser.add_argument("--pi-info", action="store_true", help="Include Pi system metrics")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    if args.config:
        config = load_config(args.config)
        checks = run_checks(config)
    else:
        checks = _default_checks()

    results = [result_to_dict(r) for r in checks]

    output: dict = {"checks": results}

    if args.pi_info:
        output["pi"] = {
            "uptime_seconds": pi_uptime(),
            "cpu_temp_celsius": pi_cpu_temp(),
        }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2)

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        for item in results:
            status = "OK  " if item["ok"] else "FAIL"
            print(f"{status} {item['name']:<16} {item['target']:<32} {item['latency_ms']:>4}ms  {item['detail']}")
        if args.pi_info:
            uptime = output["pi"]["uptime_seconds"]
            temp = output["pi"]["cpu_temp_celsius"]
            if uptime is not None:
                hours = int(uptime) // 3600
                mins = (int(uptime) % 3600) // 60
                print(f"     uptime           {hours}h {mins}m")
            if temp is not None:
                print(f"     cpu_temp         {temp:.1f}°C")

    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
