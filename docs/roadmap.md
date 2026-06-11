# Roadmap

## v0.1 — Core probes (current)

- [x] TCP reachability check with latency measurement
- [x] HTTP health check (2xx–3xx = OK)
- [x] Parallel probe execution via `ThreadPoolExecutor`
- [x] JSON config file (`config.example.json`)
- [x] Human-readable and `--json` output modes
- [x] `--pi-info` flag for uptime and CPU temperature
- [x] `--version` flag
- [x] Predictable exit codes (0 / 1) for scripting
- [x] GitHub Actions CI on Python 3.11, 3.12, and 3.13

## v0.2 — Improved observability

- [ ] Per-check consecutive-failure threshold before reporting FAIL
- [ ] Optional probe interval (`--interval N`) for continuous monitoring mode
- [ ] Summary line: total checks, pass count, elapsed time
- [ ] Write results to a JSON file (`--output FILE`) for log ingestion

## v0.3 — Extended probe types

- [ ] ICMP ping check (requires raw-socket capability or `ping` subprocess fallback)
- [ ] DNS resolution check (resolve a hostname and verify the answer)
- [ ] TLS certificate expiry check (warn N days before expiry)

## v0.4 — Notifications

- [ ] Webhook POST on failure (configurable URL in config)
- [ ] Optional SMTP alert on state change (first failure, first recovery)

## Future

- [ ] Prometheus metrics endpoint (`/metrics`) for Grafana integration
- [ ] Raspberry Pi GPIO LED indicator support
