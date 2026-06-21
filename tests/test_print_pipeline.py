"""Tests for the browser→canvas print pipeline (no hardware required)."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

from dymo_print_ui import printer_service


def _png(width: int = 40, height: int = 30) -> bytes:
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([5, 5, 15, 25], fill="black")  # a solid black block
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_build_canvas_dimensions_and_stretch() -> None:
    canvas = printer_service.build_canvas(_png(40, 30), stretch=2, dither=False)
    # Height is fixed at 30; width doubles with stretch(2).
    assert canvas.height == 30
    assert canvas.width == 80


def test_build_canvas_no_stretch() -> None:
    canvas = printer_service.build_canvas(_png(40, 30), stretch=1, dither=False)
    assert canvas.width == 40


def test_black_pixels_become_filled() -> None:
    canvas = printer_service.build_canvas(_png(40, 30), stretch=1, dither=False)
    # The drawn block at x=5..15, y=5..25 should be filled (black → True).
    assert canvas.get_pixel(10, 15) is True
    # A corner outside the block should be blank.
    assert canvas.get_pixel(38, 1) is False


def test_padding_widens_canvas() -> None:
    base = printer_service.build_canvas(_png(40, 30), stretch=1, padding=0)
    padded = printer_service.build_canvas(_png(40, 30), stretch=1, padding=10)
    assert padded.width == base.width + 20


def test_rgba_transparency_flattened_to_white() -> None:
    img = Image.new("RGBA", (20, 30), (0, 0, 0, 0))  # fully transparent
    buf = BytesIO()
    img.save(buf, format="PNG")
    canvas = printer_service.build_canvas(buf.getvalue(), stretch=1)
    # Transparent → white → no filled pixels.
    assert all(
        not canvas.get_pixel(x, y) for x in range(canvas.width) for y in range(canvas.height)
    )
