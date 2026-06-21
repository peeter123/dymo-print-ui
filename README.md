# dymo-print-ui

A local, browser-based label editor for the **Dymo LetraTag 200B**.

Design your label in the browser — text in any Google Font, Material Design
Icons, and simple shapes — preview it exactly as it will print, and send it to
the printer over Bluetooth LE.

## Quick start

```bash
poetry install
git submodule update --init        # fetch the dymo-bluetooth driver
cd frontend && npm install && npm run build && cd ..
poetry run dymo-print-ui           # serves on http://127.0.0.1:8000
```

## Development

Two processes:

```bash
poetry run uvicorn dymo_print_ui.app:app --reload   # backend on :8000
cd frontend && npm run dev                          # Vite on :5173 (open this)
```

See [CLAUDE.md](CLAUDE.md) for architecture and the driver gotchas.
