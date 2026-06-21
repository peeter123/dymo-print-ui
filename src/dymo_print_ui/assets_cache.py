"""Fetch-through disk cache for Google Fonts and MDI icons.

Two concerns live here:

* **Google Fonts** — we proxy the CSS2 stylesheet, download every referenced
  ``woff2`` into the cache, and rewrite the ``src: url(...)`` references to point
  back at our own ``/api/fonts/file/{hash}.woff2`` endpoint. After the first
  warm-up a font renders identically and works fully offline.
* **MDI icons** — served from the bundled ``@mdi/svg`` npm package (path data +
  ``meta.json``), located at import time. No network needed.

All network calls use httpx (async) so they run inside FastAPI's event loop.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import httpx
from loguru import logger
from platformdirs import user_cache_dir

APP_NAME = "dymo-print-ui"

# A modern desktop UA is required or Google serves legacy formats, not woff2.
_DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_GOOGLE_CSS2 = "https://fonts.googleapis.com/css2"
_URL_RE = re.compile(r"url\((https://[^)]+\.woff2)\)")

_cache_root = Path(user_cache_dir(APP_NAME, appauthor=False))
_fonts_dir = _cache_root / "fonts"
_css_dir = _cache_root / "css"
for _d in (_fonts_dir, _css_dir):
    _d.mkdir(parents=True, exist_ok=True)


def _hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


async def get_font_css(family_query: str) -> str:
    """Return rewritten, cached CSS for a Google Fonts ``family=`` query.

    ``family_query`` is the value of the ``family`` parameter, e.g.
    ``"Roboto:wght@400;700"``.
    """
    cache_key = _hash(family_query)
    cached = _css_dir / f"{cache_key}.css"
    if cached.exists():
        return cached.read_text(encoding="utf-8")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            _GOOGLE_CSS2,
            params={"family": family_query, "display": "swap"},
            headers={"User-Agent": _DESKTOP_UA},
        )
        resp.raise_for_status()
        css = resp.text

        # Download each referenced woff2 and rewrite its URL.
        for url in set(_URL_RE.findall(css)):
            file_hash = _hash(url)
            dest = _fonts_dir / f"{file_hash}.woff2"
            if not dest.exists():
                file_resp = await client.get(url, headers={"User-Agent": _DESKTOP_UA})
                file_resp.raise_for_status()
                dest.write_bytes(file_resp.content)
                logger.info("Cached font file {} ({} bytes)", file_hash, len(file_resp.content))
            css = css.replace(url, f"/api/fonts/file/{file_hash}.woff2")

    cached.write_text(css, encoding="utf-8")
    logger.info("Cached font CSS for {}", family_query)
    return css


def font_file_path(file_hash: str) -> Path | None:
    """Return the cached woff2 path for a hash, or None if absent."""
    # Guard against path traversal — hashes are hex only.
    if not re.fullmatch(r"[0-9a-f]{16}", file_hash):
        return None
    path = _fonts_dir / f"{file_hash}.woff2"
    return path if path.exists() else None


async def warm_font(family: str) -> bool:
    """Pre-fetch a family's weights into the cache. Returns False if unknown.

    Google's CSS2 API 400s when you request a weight a font doesn't ship (e.g.
    pixel fonts that only have 400), so we try a few queries from most to least
    specific and accept the first that succeeds.
    """
    candidates = [
        f"{family}:wght@400;700",
        f"{family}:wght@400",
        family,
    ]
    for query in candidates:
        try:
            await get_font_css(query)
            return True
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 400:
                continue  # weight not available — try a simpler query
            logger.warning("Font '{}' fetch failed ({})", family, exc.response.status_code)
            return False
    logger.warning("Font '{}' not found on Google Fonts", family)
    return False


# --------------------------------------------------------------------------- #
# MDI icons
# --------------------------------------------------------------------------- #

_mdi_svg_dir: Path | None = None
_mdi_meta: list[dict[str, Any]] | None = None


def _locate_mdi() -> Path | None:
    """Find the installed @mdi/svg package directory."""
    global _mdi_svg_dir
    if _mdi_svg_dir is not None:
        return _mdi_svg_dir
    # frontend/node_modules/@mdi/svg relative to repo root (this file is
    # src/dymo_print_ui/assets_cache.py → parents[2] is the repo root).
    repo_root = Path(__file__).resolve().parents[2]
    candidate = repo_root / "frontend" / "node_modules" / "@mdi" / "svg"
    if candidate.exists():
        _mdi_svg_dir = candidate
        return candidate
    logger.warning("@mdi/svg not found at {}; run npm install in frontend/", candidate)
    return None


def _load_mdi_meta() -> list[dict[str, Any]]:
    global _mdi_meta
    if _mdi_meta is not None:
        return _mdi_meta
    base = _locate_mdi()
    if base is None:
        _mdi_meta = []
        return _mdi_meta
    meta_path = base / "meta.json"
    try:
        _mdi_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except OSError:
        logger.warning("Could not read MDI meta.json at {}", meta_path)
        _mdi_meta = []
    return _mdi_meta


def search_icons(query: str, limit: int = 60, offset: int = 0) -> list[dict[str, str]]:
    """Search MDI icon names + aliases, with offset-based paging for lazy load.

    Empty query returns the full set in declaration order (paged).
    """
    meta = _load_mdi_meta()
    query = query.strip().lower()
    matched: list[str] = []
    for entry in meta:
        name = entry.get("name", "")
        if not query:
            matched.append(name)
        else:
            aliases = entry.get("aliases", [])
            tags = entry.get("tags", [])
            haystack = " ".join([name, *aliases, *tags]).lower()
            if query in haystack:
                matched.append(name)
    window = matched[offset : offset + limit]
    return [{"name": n} for n in window]


def icon_svg_file(name: str) -> Path | None:
    """Return the raw .svg file path for an MDI icon name, for <img>/preview use."""
    if not re.fullmatch(r"[a-z0-9-]+", name):
        return None
    base = _locate_mdi()
    if base is None:
        return None
    svg_file = base / "svg" / f"{name}.svg"
    return svg_file if svg_file.exists() else None


def icon_path_data(name: str) -> dict[str, str] | None:
    """Return SVG path data + viewBox for an MDI icon name."""
    if not re.fullmatch(r"[a-z0-9-]+", name):
        return None
    base = _locate_mdi()
    if base is None:
        return None
    svg_file = base / "svg" / f"{name}.svg"
    if not svg_file.exists():
        return None
    svg = svg_file.read_text(encoding="utf-8")
    match = re.search(r'\sd="([^"]+)"', svg)
    if not match:
        return None
    return {"path": match.group(1), "viewBox": "0 0 24 24"}
