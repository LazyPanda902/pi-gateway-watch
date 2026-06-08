# Config Example

Project: pi-gateway-watch

This is a safe sample config. Do not store secrets here.

```yaml
monitoring:
  root_path: "/"
  warning_disk_percent: 80
  critical_disk_percent: 90

reporting:
  output_format: "json"
  include_load_average: true
  include_disk_usage: true
```

## Privacy rules

- Do not include real private hostnames.
- Do not include private IP addresses.
- Do not include tokens, passwords, or `.env` values.
