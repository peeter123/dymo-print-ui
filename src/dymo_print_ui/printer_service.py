"""Printer service: the BLE bridge to the Dymo LetraTag.

Thin wrapper around the ``dymo_bluetooth`` driver. All printer access is
serialised through a single :class:`asyncio.Lock` because a BLE connection is
exclusive and slow — concurrent ``/api/print`` calls queue rather than collide.

The browser does all rendering and thresholding; by the time a PNG reaches
here it is already 1-bit black-on-white, so we convert with ``dither=False`` by
default (the opposite of the driver default) to keep the print identical to the
on-screen preview.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from io import BytesIO

from bleak import BleakScanner
from loguru import logger
from PIL import Image

from dymo_bluetooth import Canvas, Result, convert_image_to_canvas
from dymo_bluetooth.bluetooth import Printer, discover_printers

# Serialises every BLE operation across the whole process.
_printer_lock = asyncio.Lock()


class NoPrinterError(RuntimeError):
    """Raised when no printer could be found to print to."""


@dataclass
class DiscoveredPrinter:
    name: str
    mac: str


@dataclass
class PrintOutcome:
    result: str
    code: int
    low_battery: bool
    width: int
    height: int


def build_canvas(
    png_bytes: bytes,
    *,
    stretch: int = 2,
    dither: bool = False,
    padding: int = 0,
) -> Canvas:
    """Turn a rendered PNG into a print-ready :class:`Canvas`.

    Mirrors the driver's canonical sequence: convert → stretch(>=2) → pad.
    The stretch is mandatory; without it the printer renders labels too narrow.
    """
    image = Image.open(BytesIO(png_bytes))
    # Flatten any alpha onto white so transparent areas read as blank tape.
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        image = Image.alpha_composite(background, image.convert("RGBA"))
    canvas = convert_image_to_canvas(image, dither=dither)
    if stretch and stretch != 1:
        canvas = canvas.stretch(stretch)
    if padding:
        canvas = canvas.fill(padding, padding)
    return canvas


async def list_printers(max_timeout: int = 5) -> list[DiscoveredPrinter]:
    """Scan for nearby LetraTag printers."""
    async with _printer_lock:
        printers = await discover_printers(max_timeout=max_timeout)
    found = [
        DiscoveredPrinter(name=p._impl.name or "Letratag", mac=p._impl.address)
        for p in printers
    ]
    logger.info("Discovery found {} printer(s)", len(found))
    return found


async def is_reachable(mac: str, timeout: int = 4) -> bool:
    """Cheap reachability check for a known MAC — does not connect."""
    if not mac:
        return False
    device = await BleakScanner.find_device_by_address(mac, timeout=timeout)
    return device is not None


async def _acquire_printer(saved_mac: str | None, max_timeout: int) -> Printer:
    """Return a connectable Printer, preferring the saved MAC fast-path."""
    if saved_mac:
        device = await BleakScanner.find_device_by_address(saved_mac, timeout=max_timeout)
        if device is not None:
            logger.info("Using configured printer {}", saved_mac)
            return Printer(device)
        logger.warning("Configured printer {} not found; falling back to scan", saved_mac)
    printers = await discover_printers(max_timeout=max_timeout)
    if not printers:
        raise NoPrinterError("No printer found. Configure a MAC or run discovery.")
    return printers[0]


_LOW_BATTERY = {Result.SUCCESS_LOW_BATTERY, Result.FAILED_LOW_BATTERY}


async def print_canvas(
    canvas: Canvas,
    *,
    saved_mac: str | None = None,
    copies: int = 1,
    max_timeout: int = 5,
) -> PrintOutcome:
    """Connect to a printer and print ``canvas`` ``copies`` times."""
    width, height = canvas.size
    async with _printer_lock:
        printer = await _acquire_printer(saved_mac, max_timeout)
        result = Result.SUCCESS
        try:
            await printer.connect()
            for index in range(max(1, copies)):
                logger.info("Printing copy {}/{} ({}x{})", index + 1, copies, width, height)
                result = await printer.print(canvas)
                logger.info("Printer returned {}", result.name)
        finally:
            await printer.disconnect()
    return PrintOutcome(
        result=result.name,
        code=result.value,
        low_battery=result in _LOW_BATTERY,
        width=width,
        height=height,
    )
