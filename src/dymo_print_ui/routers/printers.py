"""Printer discovery and status endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from dymo_print_ui import printer_service
from dymo_print_ui.config import config

router = APIRouter(prefix="/api", tags=["printers"])


class PrinterInfo(BaseModel):
    name: str
    mac: str


class PrinterList(BaseModel):
    printers: list[PrinterInfo]


class PrinterStatus(BaseModel):
    configured_mac: str | None
    reachable: bool


@router.get("/printers", response_model=PrinterList)
async def get_printers() -> PrinterList:
    """Scan BLE for nearby LetraTag printers."""
    found = await printer_service.list_printers(max_timeout=5)
    return PrinterList(printers=[PrinterInfo(name=p.name, mac=p.mac) for p in found])


@router.get("/printer/status", response_model=PrinterStatus)
async def get_printer_status() -> PrinterStatus:
    """Report whether the configured printer is currently reachable."""
    mac = config.get("printer_mac")
    reachable = await printer_service.is_reachable(mac) if mac else False
    return PrinterStatus(configured_mac=mac, reachable=reachable)
