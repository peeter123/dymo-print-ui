import { api } from "../api";

// Cache of MDI icon name → Path2D plus its source viewBox size.
interface CachedIcon {
  path: Path2D;
  viewBox: number; // square viewBox edge (MDI is always 24)
}

const cache = new Map<string, CachedIcon>();
const pending = new Map<string, Promise<CachedIcon | null>>();

/** Fetch and cache an MDI icon's path data. Returns null if unknown. */
export async function loadIcon(name: string): Promise<CachedIcon | null> {
  const hit = cache.get(name);
  if (hit) return hit;
  const inFlight = pending.get(name);
  if (inFlight) return inFlight;

  const p = (async () => {
    try {
      const data = await api.iconPath(name);
      const edge = Number(data.viewBox.split(" ")[2]) || 24;
      const icon: CachedIcon = { path: new Path2D(data.path), viewBox: edge };
      cache.set(name, icon);
      return icon;
    } catch {
      return null;
    } finally {
      pending.delete(name);
    }
  })();
  pending.set(name, p);
  return p;
}

/** Synchronous lookup for already-loaded icons (used in the render loop). */
export function getCachedIcon(name: string): CachedIcon | null {
  return cache.get(name) ?? null;
}

/** Draw an icon centred in a square of `sizePx` at (x, y) on the context. */
export function drawIcon(
  ctx: CanvasRenderingContext2D,
  icon: CachedIcon,
  x: number,
  y: number,
  sizePx: number,
): void {
  const scale = sizePx / icon.viewBox;
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(scale, scale);
  ctx.fillStyle = "#000";
  ctx.fill(icon.path);
  ctx.restore();
}
