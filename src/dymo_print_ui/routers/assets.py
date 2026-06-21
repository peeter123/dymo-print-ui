"""Font + icon proxy/cache endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from dymo_print_ui import assets_cache
from dymo_print_ui.config import config

router = APIRouter(prefix="/api", tags=["assets"])


class FontList(BaseModel):
    fonts: list[str]


class AddFont(BaseModel):
    family: str


# --------------------------------------------------------------------------- #
# Fonts
# --------------------------------------------------------------------------- #


@router.get("/fonts", response_model=FontList)
async def get_fonts() -> FontList:
    return FontList(fonts=config.get("fonts", []))


@router.post("/fonts", response_model=FontList)
async def add_font(body: AddFont) -> FontList:
    family = body.family.strip()
    if not family:
        raise HTTPException(status_code=400, detail="Empty font family.")
    ok = await assets_cache.warm_font(family)
    if not ok:
        raise HTTPException(status_code=404, detail=f"'{family}' not found on Google Fonts.")
    fonts: list[str] = config.get("fonts", [])
    if family not in fonts:
        fonts = [*fonts, family]
        config.set("fonts", fonts)
    return FontList(fonts=fonts)


@router.delete("/fonts/{family}", response_model=FontList)
async def remove_font(family: str) -> FontList:
    fonts: list[str] = [f for f in config.get("fonts", []) if f != family]
    config.set("fonts", fonts)
    return FontList(fonts=fonts)


@router.get("/fonts/css")
async def font_css(family: str = Query(...)) -> Response:
    """Proxy + cache the Google Fonts CSS for a ``family`` query."""
    try:
        css = await assets_cache.get_font_css(family)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Font fetch failed: {exc}") from exc
    return Response(content=css, media_type="text/css")


@router.get("/fonts/file/{file_hash}.woff2")
async def font_file(file_hash: str) -> FileResponse:
    path = assets_cache.font_file_path(file_hash)
    if path is None:
        raise HTTPException(status_code=404, detail="Font file not cached.")
    return FileResponse(path, media_type="font/woff2")


# --------------------------------------------------------------------------- #
# Icons
# --------------------------------------------------------------------------- #


@router.get("/icons")
async def get_icons(q: str = Query("", alias="q"), limit: int = 60, offset: int = 0) -> dict:
    return {"icons": assets_cache.search_icons(q, limit=limit, offset=offset)}


@router.get("/icons/{name}.svg")
async def get_icon_svg(name: str) -> FileResponse:
    """Serve the raw SVG so it can be used directly in <img> previews."""
    path = assets_cache.icon_svg_file(name)
    if path is None:
        raise HTTPException(status_code=404, detail=f"Icon '{name}' not found.")
    return FileResponse(path, media_type="image/svg+xml")


@router.get("/icons/{name}")
async def get_icon(name: str) -> dict:
    data = assets_cache.icon_path_data(name)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Icon '{name}' not found.")
    return {"name": name, **data}
