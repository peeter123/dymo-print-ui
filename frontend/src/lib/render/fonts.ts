import { api } from "../api";
import { getFontSpec, fontQuery } from "./fontRegistry";

// Track which @font-face stylesheets we've already injected.
const injected = new Set<string>();
const loaded = new Set<string>();

/** Inject the proxied Google Fonts stylesheet for a family (idempotent).
 *
 * The query asks for only the weights/styles the font actually ships (per the
 * font registry) — requesting an absent weight makes Google's CSS2 API 400 and
 * the whole font fails to load, which is what broke pixel fonts. */
export function injectFont(family: string): void {
  if (injected.has(family)) return;
  injected.add(family);
  const query = fontQuery(getFontSpec(family));
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = `/api/fonts/css?family=${encodeURIComponent(query)}`;
  document.head.appendChild(link);
}

/** Inject all configured fonts at startup. */
export function injectFonts(families: string[]): void {
  for (const f of families) injectFont(f);
}

/** Inject the UI chrome font (Inter) — independent of the label font list,
 * which now contains only pixel fonts. */
export function injectUiFont(): void {
  if (injected.has("__ui__")) return;
  injected.add("__ui__");
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = `/api/fonts/css?family=${encodeURIComponent("Inter:wght@400;500;600;700")}`;
  document.head.appendChild(link);
}

/**
 * Ensure a font is actually ready to rasterise before we draw to the export
 * canvas — otherwise the first render silently uses a fallback face.
 */
export async function ensureFontLoaded(
  family: string,
  weight = 400,
  italic = false,
): Promise<void> {
  injectFont(family);
  const key = `${family}-${weight}-${italic}`;
  if (loaded.has(key)) return;
  const style = italic ? "italic " : "";
  try {
    await document.fonts.load(`${style}${weight} 24px "${family}"`);
    loaded.add(key);
  } catch {
    /* fall back to whatever the browser substitutes */
  }
}

/** Add a new font family via the backend and inject it. */
export async function addFont(family: string): Promise<string[]> {
  const fonts = await api.addFont(family);
  injectFont(family);
  return fonts;
}
