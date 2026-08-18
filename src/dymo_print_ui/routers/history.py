"""Print history endpoints: list, recall, save-as-draft, reprint, delete."""

from __future__ import annotations

import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel

from dymo_print_ui import printer_service
from dymo_print_ui.config import config
from dymo_print_ui.history_store import history
from dymo_print_ui.printer_service import NoPrinterError

router = APIRouter(prefix="/api", tags=["history"])


class HistoryEntrySummary(BaseModel):
    id: str
    timestamp: str
    width: int
    height: int


class HistoryEntryDetail(HistoryEntrySummary):
    document: dict


class HistoryList(BaseModel):
    entries: list[HistoryEntrySummary]


def _summary(entry) -> HistoryEntrySummary:
    return HistoryEntrySummary(
        id=entry.id, timestamp=entry.timestamp, width=entry.width, height=entry.height
    )


@router.get("/history", response_model=HistoryList)
async def list_history() -> HistoryList:
    return HistoryList(entries=[_summary(e) for e in history.list()])


@router.get("/history/{entry_id}", response_model=HistoryEntryDetail)
async def get_history_entry(entry_id: str) -> HistoryEntryDetail:
    entry = history.get(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found.")
    return HistoryEntryDetail(
        id=entry.id,
        timestamp=entry.timestamp,
        width=entry.width,
        height=entry.height,
        document=entry.document,
    )


@router.get("/history/{entry_id}/thumbnail.png")
async def get_history_thumbnail(entry_id: str) -> FileResponse:
    path = history.png_path(entry_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Thumbnail not found.")
    return FileResponse(path, media_type="image/png")


@router.delete("/history/{entry_id}")
async def delete_history_entry(entry_id: str) -> dict:
    if not history.delete(entry_id):
        raise HTTPException(status_code=404, detail="History entry not found.")
    return {"deleted": entry_id}


@router.post("/history", response_model=HistoryEntrySummary)
async def save_history_draft(
    image: UploadFile = File(...),
    document: str = Form(...),
    stretch: int = Form(2),
    dither: bool = Form(False),
    padding: int = Form(0),
) -> HistoryEntrySummary:
    """Save the current editor state to history without printing it."""
    png_bytes = await image.read()
    canvas = printer_service.build_canvas(
        png_bytes, stretch=stretch, dither=dither, padding=padding
    )
    width, height = canvas.size
    entry = history.add(
        png_bytes=png_bytes,
        document=json.loads(document),
        width=width,
        height=height,
        stretch=stretch,
        dither=dither,
        padding=padding,
    )
    return _summary(entry)


@router.post("/history/{entry_id}/reprint")
async def reprint_history_entry(entry_id: str, copies: int = Form(1)) -> dict:
    """Replay the exact stored PNG through the print pipeline. No re-render."""
    entry = history.get(entry_id)
    png_path = history.png_path(entry_id)
    if entry is None or png_path is None:
        raise HTTPException(status_code=404, detail="History entry not found.")
    canvas = printer_service.build_canvas(
        png_path.read_bytes(), stretch=entry.stretch, dither=entry.dither, padding=entry.padding
    )
    try:
        outcome = await printer_service.print_canvas(
            canvas, saved_mac=config.get("printer_mac"), copies=copies
        )
    except NoPrinterError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Reprint failed")
        raise HTTPException(status_code=502, detail=f"Print failed: {exc}") from exc
    return {
        "result": outcome.result,
        "code": outcome.code,
        "low_battery": outcome.low_battery,
        "width": outcome.width,
        "height": outcome.height,
    }
