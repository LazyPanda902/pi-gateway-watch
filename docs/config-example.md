# Config Reference

Copy `config.example.json` from the project root and edit it for your targets.

## TCP check

```json
{
  "name": "dns",
  "type": "tcp",
  "host": "1.1.1.1",
  "port": 53,
  "timeout": 2.0
}
```

## HTTP check

```json
{
  "name": "web",
  "type": "http",
  "url": "https://example.com",
  "timeout": 3.0
}
```

## Full example

```json
{
  "checks": [
    {"name": "dns",  "type": "tcp",  "host": "1.1.1.1",     "port": 53},
    {"name": "web",  "type": "http", "url": "https://example.com"},
    {"name": "ntp",  "type": "tcp",  "host": "pool.ntp.org", "port": 123}
  ]
}
```

Run with:

```bash
python src/app.py --config my-checks.json
```

Only use public or test-safe targets in files committed to version control.
