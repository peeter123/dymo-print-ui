import type { Box, LabelElement, TextElement } from "../types";
import { TAPE_HEIGHT, MM_PER_PX } from "../types";
import { getCachedIcon } from "./icons";

/** Build the canvas font shorthand for a text element. */
export function fontString(el: TextElement): string {
  const style = el.italic ? "italic " : "";
  return `${style}${el.weight} ${el.fontPx}px "${el.fontFamily}", sans-serif`;
}

// A shared offscreen context purely for text measurement.
let measureCtx: CanvasRenderingContext2D | null = null;
function ctx(): CanvasRenderingContext2D {
  if (!measureCtx) {
    const c = document.createElement("canvas");
    measureCtx = c.getContext("2d")!;
  }
  return measureCtx;
}

/** Measured width of a text element including letter spacing. */
export function textWidth(el: TextElement): number {
  const c = ctx();
  c.font = fontString(el);
  const base = c.measureText(el.text).width;
  const spacing = el.letterSpacing * Math.max(0, el.text.length - 1);
  return base + spacing;
}

/**
 * Vertical metrics for a text element, in tape pixels. Uses the *font* bounding
 * box (constant for a font+size, independent of the specific glyphs) rather than
 * the per-string actual box, so the selection box is stable while typing and —
 * crucially — matches exactly how `drawElements` positions the baseline. The two
 * MUST agree or the glyphs spill outside the selection outline.
 */
export function textVMetrics(el: TextElement): { ascent: number; descent: number } {
  const c = ctx();
  c.font = fontString(el);
  const m = c.measureText(el.text || "M");
  const ascent = m.fontBoundingBoxAscent || m.actualBoundingBoxAscent || el.fontPx * 0.8;
  const descent = m.fontBoundingBoxDescent || m.actualBoundingBoxDescent || el.fontPx * 0.2;
  return { ascent, descent };
}

/** Full line-box height of a text element. */
export function textHeight(el: TextElement): number {
  const { ascent, descent } = textVMetrics(el);
  return ascent + descent;
}

/**
 * Vertical extent of a text element's box, matching exactly how `drawElements`
 * places it: the baseline is `round(el.y + ascent)`, glyphs occupy
 * [baseline - ascent, baseline + descent]. Deriving the box from the same
 * rounded baseline keeps descenders from spilling past the selection outline.
 */
export function textBoxV(el: TextElement): { top: number; height: number } {
  const { ascent, descent } = textVMetrics(el);
  const baseline = Math.round(el.y + ascent);
  const top = baseline - ascent;
  return { top, height: Math.ceil(ascent + descent) };
}

/** The axis-aligned bounding box of an element, in tape pixels. */
export function elementBox(el: LabelElement): Box {
  switch (el.type) {
    case "text": {
      const v = textBoxV(el);
      return { x: el.x, y: v.top, w: textWidth(el), h: v.height };
    }
    case "icon":
      return { x: el.x, y: el.y, w: el.sizePx, h: el.sizePx };
    case "rect":
      return { x: el.x, y: el.y, w: el.w, h: el.h };
    case "line": {
      // The stroke is centred on the path and uses round caps, so it extends
      // lineWidth/2 beyond the path on every side. Grow the box to match.
      const half = el.lineWidth / 2;
      const x = Math.min(el.x, el.x + el.dx) - half;
      const y = Math.min(el.y, el.y + el.dy) - half;
      return {
        x,
        y,
        w: Math.abs(el.dx) + el.lineWidth,
        h: Math.abs(el.dy) + el.lineWidth,
      };
    }
  }
}

/** The right-most content extent across all elements (0 if empty). */
export function contentExtent(elements: LabelElement[]): number {
  let max = 0;
  for (const el of elements) {
    const box = elementBox(el);
    max = Math.max(max, box.x + box.w);
  }
  return Math.ceil(max);
}

/** Total tape width = content extent + both margins, min 1px. */
export function tapeWidth(
  elements: LabelElement[],
  marginLeft: number,
  marginRight: number,
): number {
  return Math.max(1, contentExtent(elements) + marginLeft + marginRight);
}

/** Estimated physical length in mm after the server stretch. */
export function tapeLengthMm(widthPx: number, stretch: number): number {
  return widthPx * stretch * MM_PER_PX;
}

export { TAPE_HEIGHT };
