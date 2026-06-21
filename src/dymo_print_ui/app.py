"""FastAPI application factory.

In development the Svelte app is served by Vite on :5173 and proxies ``/api`` to
this server. In production the built SPA in ``frontend/dist`` is mounted here and
served with an ``index.html`` fallback for client-side routing.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from dymo_print_ui.logging import setup_logging
from dymo_print_ui.routers import assets, config, printers, printing

_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Dymo Print UI", version="0.1.0")

    # Dev convenience: Vite (5173) talking to uvicorn (8000).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(printers.router)
    app.include_router(printing.router)
    app.include_router(config.router)
    app.include_router(assets.router)

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok"}

    _mount_frontend(app)
    return app


def _mount_frontend(app: FastAPI) -> None:
    """Serve the built SPA with a history-mode fallback, if it exists."""
    if not _FRONTEND_DIST.exists():
        return

    assets_dir = _FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    index_file = _FRONTEND_DIST / "index.html"

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        # Serve a real file if it exists (favicon etc.), else index.html.
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_file)


app = create_app()
