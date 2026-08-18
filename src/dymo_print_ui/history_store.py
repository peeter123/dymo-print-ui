"""Persistent print history: thumbnails + label documents on disk.

Every successful print (and every explicit "save to history" from the editor)
is recorded here so it can be recalled later — either replayed bit-for-bit
(reprint) or loaded back into the editor for further changes. Storage mirrors
:class:`dymo_print_ui.config.ConfigStore`'s atomic-write JSON pattern, but
lives under ``user_data_dir`` rather than ``user_config_dir`` since it holds a
growing list of entries rather than a handful of settings, and under
``user_data_dir`` rather than a cache dir since it is not re-derivable data.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from loguru import logger
from platformdirs import user_data_dir

APP_NAME = "dymo-print-ui"

_ID_RE = re.compile(r"[0-9a-f]{32}")


@dataclass
class HistoryEntry:
    id: str
    timestamp: str
    document: dict[str, Any]
    width: int
    height: int
    stretch: int
    dither: bool
    padding: int


class HistoryStore:
    """Thread-safe JSON-index + one-PNG-per-entry history store."""

    def __init__(self, data_dir: Path | None = None) -> None:
        if data_dir is None:
            data_dir = Path(user_data_dir(APP_NAME, appauthor=False))
        self.data_dir = data_dir
        self.png_dir = data_dir / "history"
        self.index_path = data_dir / "history.json"
        self.png_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._entries: list[HistoryEntry] = []
        self._load()

    def _load(self) -> None:
        if not self.index_path.exists():
            return
        try:
            raw = json.loads(self.index_path.read_text(encoding="utf-8"))
            self._entries = [HistoryEntry(**item) for item in raw]
        except (json.JSONDecodeError, OSError, TypeError) as exc:
            logger.warning("History index unreadable ({}); starting empty", exc)
            self._entries = []

    def _save(self) -> None:
        fd, tmp = tempfile.mkstemp(dir=str(self.data_dir), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump([asdict(e) for e in self._entries], fh, indent=2)
            os.replace(tmp, self.index_path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def list(self) -> list[HistoryEntry]:
        with self._lock:
            return sorted(self._entries, key=lambda e: e.timestamp, reverse=True)

    def get(self, entry_id: str) -> HistoryEntry | None:
        with self._lock:
            return next((e for e in self._entries if e.id == entry_id), None)

    def png_path(self, entry_id: str) -> Path | None:
        if not _ID_RE.fullmatch(entry_id):
            return None
        path = self.png_dir / f"{entry_id}.png"
        return path if path.exists() else None

    def add(
        self,
        *,
        png_bytes: bytes,
        document: dict[str, Any],
        width: int,
        height: int,
        stretch: int,
        dither: bool,
        padding: int,
    ) -> HistoryEntry:
        entry = HistoryEntry(
            id=uuid.uuid4().hex,
            timestamp=datetime.now(timezone.utc).isoformat(),
            document=document,
            width=width,
            height=height,
            stretch=stretch,
            dither=dither,
            padding=padding,
        )
        with self._lock:
            (self.png_dir / f"{entry.id}.png").write_bytes(png_bytes)
            self._entries.append(entry)
            self._save()
        logger.info("Recorded history entry {}", entry.id)
        return entry

    def delete(self, entry_id: str) -> bool:
        with self._lock:
            match = next((e for e in self._entries if e.id == entry_id), None)
            if match is None:
                return False
            self._entries.remove(match)
            self._save()
        png = self.png_dir / f"{entry_id}.png"
        if png.exists():
            png.unlink()
        return True


# Module-level singleton used by the routers.
history = HistoryStore()
