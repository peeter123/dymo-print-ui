import type { TextElement } from "../types";

/**
 * Per-font metadata. Two problems this solves:
 *
 * 1. **Correct loading** — Google's CSS2 API 400s if you request a weight a font
 *    doesn't have. Pixel fonts ship a single weight (400), so we must request
 *    exactly what exists or the font silently fails to load.
 * 2. **Pixel-perfect sizing** — a pixel font only renders crisply at integer
 *    multiples of its design grid. For these fonts we expose grid-locked S/M/L
 *    sizes instead of a free slider, so text always lands on the pixel grid.
 */
export interface FontSpec {
  family: string;
  weights: number[];
  italic: boolean;
  pixel: boolean;
  /** Grid-locked S, M, L pixel sizes (pixel fonts only). */
  gridSizes?: [number, number, number];
}

export const FONT_REGISTRY: Record<string, FontSpec> = {
  // Pixel / bitmap faces only. These render perfectly sharp (no anti-aliasing)
  // at their grid-locked sizes, which is what the 30px 1-bit tape needs.
  "Pixelify Sans": {
    family: "Pixelify Sans",
    weights: [400, 500, 600, 700],
    italic: false,
    pixel: true,
    gridSizes: [12, 18, 24],
  },
  "Press Start 2P": {
    family: "Press Start 2P",
    weights: [400],
    italic: false,
    pixel: true,
    gridSizes: [8, 16, 24],
  },
  Silkscreen: {
    family: "Silkscreen",
    weights: [400, 700],
    italic: false,
    pixel: true,
    gridSizes: [8, 16, 24],
  },
  "Jersey 10": {
    family: "Jersey 10",
    weights: [400],
    italic: false,
    pixel: true,
    gridSizes: [8, 16, 24],
  },
  Tiny5: {
    family: "Tiny5",
    weights: [400],
    italic: false,
    pixel: true,
    gridSizes: [8, 16, 24],
  },
};

/** Spec for any family — unknown (user-added) fonts default to a safe 400-only face. */
export function getFontSpec(family: string): FontSpec {
  return FONT_REGISTRY[family] ?? { family, weights: [400], italic: false, pixel: false };
}

/** Build the Google CSS2 `family=` query for a spec, requesting only real axes. */
export function fontQuery(spec: FontSpec): string {
  if (spec.italic) {
    const parts = [
      ...spec.weights.map((w) => `0,${w}`),
      ...spec.weights.map((w) => `1,${w}`),
    ];
    return `${spec.family}:ital,wght@${parts.join(";")}`;
  }
  return `${spec.family}:wght@${spec.weights.join(";")}`;
}

/** Nearest grid size to a target (pixel fonts). */
function nearestGrid(sizes: [number, number, number], target: number): number {
  return sizes.reduce((a, b) => (Math.abs(b - target) < Math.abs(a - target) ? b : a));
}

/**
 * Coerce a text element to be valid for a (possibly newly chosen) font: clamp
 * the weight to one the font has, drop italic if unsupported, and snap the size
 * to the font's pixel grid. Returns only the fields that need changing.
 */
export function normalizeForFont(t: TextElement, spec: FontSpec): Partial<TextElement> {
  const patch: Partial<TextElement> = {};
  if (!spec.weights.includes(t.weight)) {
    patch.weight = spec.weights.includes(400) ? 400 : spec.weights[0];
  }
  if (!spec.italic && t.italic) patch.italic = false;
  if (spec.pixel && spec.gridSizes) {
    if (!spec.gridSizes.includes(t.fontPx)) patch.fontPx = nearestGrid(spec.gridSizes, t.fontPx);
    if (t.letterSpacing !== 0) patch.letterSpacing = 0; // off-grid spacing breaks alignment
  }
  return patch;
}
