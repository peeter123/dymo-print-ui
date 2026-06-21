"""Entry point: launch the server and open the browser.

Run via the Poetry script ``dymo-print-ui`` (production, serves the built SPA on
:8000) or ``python -m dymo_print_ui``.
"""

from __future__ import annotations

import threading
import webbrowser

import uvicorn

HOST = "127.0.0.1"
PORT = 8000


def _open_browser() -> None:
    webbrowser.open(f"http://{HOST}:{PORT}")


def main() -> None:
    threading.Timer(1.5, _open_browser).start()
    uvicorn.run("dymo_print_ui.app:app", host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
