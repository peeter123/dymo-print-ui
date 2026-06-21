import type { LabelElement } from "../types";
import { TAPE_HEIGHT } from "../types";
import { fontString, textVMetrics } from "./measure";
import { getCachedIcon, drawIcon } from "./icons";

/**
 * Draw every element onto a 2D context in tape-pixel coordinates. The caller
 * sets up scaling/translation; this routine assumes (0,0) is the tape origin
 * and draws pure black on whatever background the caller filled.
 *
 * Used by both the editor's display canvas (scaled up) and the authoritative
 * export canvas (1:1) so the two can never drift.
 */
export function drawElements(ctx: CanvasRenderingContext2D, elements: LabelElement[]): void {
  ctx.fillStyle = "#000";
  ctx.strokeStyle = "#000";

  for (const el of elements) {
    switch (el.type) {
      case "text": {
        ctx.font = fontString(el);
        ctx.fillStyle = "#000";
        // Pixel-grid alignment: position by the *baseline* and snap it to an
        // integer tape pixel. With textBaseline="top" the canvas aligns the
        // em-box top (a fractional ascent metric) to el.y, leaving the glyph
        // rows on a sub-pixel offset — fatal for pixel fonts. Drawing on a
        // rounded baseline puts every glyph row back on the grid. The ascent
        // here is the *font* bounding-box ascent — the same metric measure.ts
        // uses for the selection box, so glyphs never spill outside it.
        ctx.textBaseline = "alphabetic";
        const baseline = Math.round(el.y + textVMetrics(el).ascent);
        if (el.letterSpacing) {
          // Manual letter spacing for consistent measurement.
          let x = el.x;
          for (const ch of el.text) {
            ctx.fillText(ch, x, baseline);
            x += ctx.measureText(ch).width + el.letterSpacing;
          }
        } else {
          ctx.fillText(el.text, el.x, baseline);
        }
        break;
      }
      case "icon": {
        const icon = getCachedIcon(el.mdiName);
        if (icon) {
          drawIcon(ctx, icon, el.x, el.y, el.sizePx);
        } else {
          // Placeholder box until the path data arrives.
          ctx.strokeStyle = "#000";
          ctx.lineWidth = 1;
          ctx.strokeRect(el.x + 0.5, el.y + 0.5, el.sizePx - 1, el.sizePx - 1);
        }
        break;
      }
      case "rect": {
        ctx.lineWidth = el.lineWidth;
        if (el.filled) {
          ctx.fillStyle = "#000";
          ctx.fillRect(el.x, el.y, el.w, el.h);
        } else {
          ctx.strokeStyle = "#000";
          const o = el.lineWidth / 2;
          ctx.strokeRect(el.x + o, el.y + o, el.w - el.lineWidth, el.h - el.lineWidth);
        }
        break;
      }
      case "line": {
        ctx.strokeStyle = "#000";
        ctx.lineWidth = el.lineWidth;
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(el.x, el.y);
        ctx.lineTo(el.x + el.dx, el.y + el.dy);
        ctx.stroke();
        break;
      }
    }
  }
}

export { TAPE_HEIGHT };
