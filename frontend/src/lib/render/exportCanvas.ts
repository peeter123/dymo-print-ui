import type { LabelDoc } from "../stores/label";
import type { LabelElement, TextElement, IconElement } from "../types";
import { TAPE_HEIGHT } from "../types";
import { drawElements } from "./draw";
import { tapeWidth } from "./measure";
import { ensureFontLoaded } from "./fonts";
import { loadIcon } from "./icons";

/**
 * Render a label document to an authoritative width×30 1-bit bitmap.
 *
 * This is the WYSIWYG contract: the same canvas this produces feeds both the
 * on-screen preview and the print POST, so preview == print. Thresholding to
 * pure black/white happens here in JS, which is why the backend prints with
 * dither disabled.
 */
export async function renderExportCanvas(doc: LabelDoc): Promise<HTMLCanvasElement> {
  await ensureAssetsReady(doc.elements);

  const width = tapeWidth(doc.elements, doc.marginLeft, doc.marginRight);
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = TAPE_HEIGHT;
  const ctx = canvas.getContext("2d", { willReadFrequently: true })!;

  // White tape background.
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, width, TAPE_HEIGHT);

  // Content is laid out from the left margin inward.
  ctx.save();
  ctx.translate(doc.marginLeft, 0);
  drawElements(ctx, doc.elements);
  ctx.restore();

  thresholdToBinary(ctx, width, TAPE_HEIGHT);
  return canvas;
}

/** Wait until every font + icon used in the doc is loaded and cacheable. */
export async function ensureAssetsReady(elements: LabelElement[]): Promise<void> {
  const jobs: Promise<unknown>[] = [];
  for (const el of elements) {
    if (el.type === "text") {
      const t = el as TextElement;
      jobs.push(ensureFontLoaded(t.fontFamily, t.weight, t.italic));
    } else if (el.type === "icon") {
      jobs.push(loadIcon((el as IconElement).mdiName));
    }
  }
  await Promise.all(jobs);
}

/** Threshold every pixel to pure black or white at luminance 128. */
export function thresholdToBinary(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
): void {
  const img = ctx.getImageData(0, 0, width, height);
  const d = img.data;
  for (let i = 0; i < d.length; i += 4) {
    // Rec. 601 luma; treat transparent as white.
    const a = d[i + 3];
    const lum =
      a === 0 ? 255 : 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
    const v = lum < 128 ? 0 : 255;
    d[i] = d[i + 1] = d[i + 2] = v;
    d[i + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
}

/** Render the doc and return a PNG blob ready to POST. */
export async function renderToPng(doc: LabelDoc): Promise<Blob> {
  const canvas = await renderExportCanvas(doc);
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error("Failed to encode PNG"));
    }, "image/png");
  });
}
