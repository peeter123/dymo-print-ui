"""Printing and (hardware-free) preview endpoints."""

from __future__ import annotations

import json
from io import BytesIO

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from loguru import logger

from dymo_print_ui import printer_service
from dymo_print_ui.config import config
from dymo_print_ui.history_store import history
from dymo_print_ui.printer_service import NoPrinterError

router = APIRouter(prefix="/api", tags=["printing"])


@router.post("/print")
async def print_label(
    image: UploadFile = File(...),
    copies: int = Form(1),
    stretch: int = Form(2),
    dither: bool = Form(False),
    padding: int = Form(0),
    document: str | None = Form(None),
) -> dict:
    """Receive a browser-rendered PNG and print it on the LetraTag."""
    png_bytes = await image.read()
    canvas = printer_service.build_canvas(
        png_bytes, stretch=stretch, dither=dither, padding=padding
    )
    try:
        outcome = await printer_service.print_canvas(
            canvas,
            saved_mac=config.get("printer_mac"),
            copies=copies,
        )
    except NoPrinterError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # BLE / GATT failures surface as 502.
        logger.exception("Print failed")
        raise HTTPException(status_code=502, detail=f"Print failed: {exc}") from exc

    if outcome.result.startswith("SUCCESS") and document is not None:
        try:
            history.add(
                png_bytes=png_bytes,
                document=json.loads(document),
                width=outcome.width,
                height=outcome.height,
                stretch=stretch,
                dither=dither,
                padding=padding,
            )
        except Exception:
            logger.exception("Failed to record print history (print itself succeeded)")

    return {
        "result": outcome.result,
        "code": outcome.code,
        "low_battery": outcome.low_battery,
        "width": outcome.width,
        "height": outcome.height,
    }


@router.post("/print/preview")
async def preview_label(
    image: UploadFile = File(...),
    stretch: int = Form(2),
    dither: bool = Form(False),
    padding: int = Form(0),
) -> Response:
    """Run the exact print pipeline minus BLE and return the 1-bit PNG.

    Lets the UI (and tests) confirm preview == print without a printer. The
    returned image is the post-threshold monochrome canvas the printer receives,
    rendered back to PNG at the *un-stretched* resolution for easy comparison.
    """
    from PIL import Image

    png_bytes = await image.read()
    canvas = printer_service.build_canvas(
        png_bytes, stretch=stretch, dither=dither, padding=padding
    )
    width, height = canvas.size
    # Rebuild a viewable PNG from the canvas pixels.
    out = Image.new("1", (width, height), color=1)
    for x in range(width):
        for y in range(height):
            if canvas.get_pixel(x, y):
                out.putpixel((x, y), 0)
    buf = BytesIO()
    out.save(buf, format="PNG")
    return Response(
        content=buf.getvalue(),
        media_type="image/png",
        headers={"X-Canvas-Width": str(width), "X-Canvas-Height": str(height)},
    )
