"""Persistent application configuration.

Stored as JSON under the user's config directory
(``%APPDATA%\\dymo-print-ui\\config.json`` on Windows). Writes are atomic so a
crash mid-save can never corrupt the file. The store is intentionally tiny and
human-editable; cached font/icon assets live elsewhere (see
:mod:`dymo_print_ui.assets_cache`).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import Lock
from typing import Any

from loguru import logger
from platformdirs import user_config_dir

APP_NAME = "dymo-print-ui"

# Fonts every install ships with. All are pixel/bitmap faces: they render
# perfectly sharp (no anti-aliasing) at their grid-locked sizes, which is ideal
# for the 30px 1-bit tape. Grid sizes live in the frontend font registry.
DEFAULT_FONTS: list[str] = [
    "Pixelify Sans",
    "Press Start 2P",
    "Silkscreen",
    "Jersey 10",
    "Tiny5",
]

# Fonts we shipped as defaults in earlier versions but have since dropped. They
# are pruned from existing configs on load (unless the user re-added them, which
# we can't distinguish — acceptable since they were never great on the tape).
RETIRED_DEFAULT_FONTS: list[str] = [
    "Inter",
    "Roboto",
    "Roboto Mono",
    "JetBrains Mono",
    "Space Mono",
    "DM Mono",
    "Oswald",
    "Bebas Neue",
    "Lobster",
    "VT323",
]

DEFAULTS: dict[str, Any] = {
    "printer_mac": None,
    "printer_name": None,
    "default_stretch": 2,
    "default_dither": False,
    "fonts": DEFAULT_FONTS,
}


class ConfigStore:
    """Thread-safe JSON-backed key/value store with atomic writes."""

    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            config_dir = Path(user_config_dir(APP_NAME, appauthor=False))
            config_dir.mkdir(parents=True, exist_ok=True)
            path = config_dir / "config.json"
        self.path = path
        self._lock = Lock()
        self._data: dict[str, Any] = dict(DEFAULTS)
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            logger.info("No config found, writing defaults to {}", self.path)
            self._save()
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Config unreadable ({}); falling back to defaults", exc)
            return
        # Merge so newly-added default keys appear for old config files.
        self._data = {**DEFAULTS, **loaded}
        # Reconcile the font list: ensure shipped defaults are present, prune
        # fonts we've since retired, and preserve any genuinely user-added ones.
        user_fonts = loaded.get("fonts", [])
        extra = [
            f
            for f in user_fonts
            if f not in DEFAULT_FONTS and f not in RETIRED_DEFAULT_FONTS
        ]
        merged_fonts = [*DEFAULT_FONTS, *extra]
        if merged_fonts != user_fonts:
            self._data["fonts"] = merged_fonts
            self._save()

    def _save(self) -> None:
        # Atomic write: temp file in the same dir, then os.replace.
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def all(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def update(self, values: dict[str, Any]) -> dict[str, Any]:
        """Merge ``values`` into the config and persist. Returns full config."""
        with self._lock:
            self._data.update({k: v for k, v in values.items() if v is not None})
            self._save()
            return dict(self._data)

    def set(self, key: str, value: Any) -> dict[str, Any]:
        return self.update({key: value})


# Module-level singleton used by the routers.
config = ConfigStore()
