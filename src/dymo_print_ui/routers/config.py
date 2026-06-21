"""Configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from dymo_print_ui.config import config

router = APIRouter(prefix="/api", tags=["config"])


class ConfigPatch(BaseModel):
    printer_mac: str | None = None
    printer_name: str | None = None
    default_stretch: int | None = None
    default_dither: bool | None = None
    fonts: list[str] | None = None


class PrinterChoice(BaseModel):
    mac: str
    name: str | None = None


@router.get("/config")
async def get_config() -> dict:
    return config.all()


@router.put("/config")
async def put_config(patch: ConfigPatch) -> dict:
    return config.update(patch.model_dump(exclude_none=True))


@router.post("/config/printer")
async def set_printer(choice: PrinterChoice) -> dict:
    """Save the selected printer (from the discovery page or manual entry)."""
    return config.update({"printer_mac": choice.mac, "printer_name": choice.name})
