import type { Box, LabelElement } from "../types";
import { TAPE_HEIGHT } from "../types";
import { elementBox } from "./measure";

export interface Guide {
  axis: "x" | "y";
  pos: number; // tape-pixel coordinate of the guide line
}

export interface SnapResult {
  x: number;
  y: number;
  guides: Guide[];
}

const THRESHOLD = 3; // tape pixels of magnetism

/**
 * Snap a moving element's top-left (x, y) to alignment targets: the tape's
 * vertical centre and top/bottom edges, plus the edges and centres of other
 * elements. Returns the adjusted position and the guide lines to draw.
 */
export function snapPosition(
  moving: LabelElement,
  others: LabelElement[],
  proposed: { x: number; y: number },
): SnapResult {
  const box = elementBox({ ...moving, x: proposed.x, y: proposed.y } as LabelElement);

  // Candidate vertical (x) targets and horizontal (y) targets.
  const xTargets: number[] = [];
  const yTargets: number[] = [TAPE_HEIGHT / 2, 0, TAPE_HEIGHT];

  for (const o of others) {
    const b = elementBox(o);
    xTargets.push(b.x, b.x + b.w, b.x + b.w / 2);
    yTargets.push(b.y, b.y + b.h, b.y + b.h / 2);
  }

  const guides: Guide[] = [];
  let x = proposed.x;
  let y = proposed.y;

  // Snap X: try left edge, centre, right edge of the moving box.
  const xEdges = [
    { offset: 0, val: box.x },
    { offset: box.w / 2, val: box.x + box.w / 2 },
    { offset: box.w, val: box.x + box.w },
  ];
  let bestX: { dist: number; pos: number; guide: number } | null = null;
  for (const edge of xEdges) {
    for (const t of xTargets) {
      const dist = Math.abs(edge.val - t);
      if (dist <= THRESHOLD && (!bestX || dist < bestX.dist)) {
        bestX = { dist, pos: proposed.x + (t - edge.val), guide: t };
      }
    }
  }
  if (bestX) {
    x = bestX.pos;
    guides.push({ axis: "x", pos: bestX.guide });
  }

  // Snap Y: top edge, centre, bottom edge.
  const yEdges = [
    { offset: 0, val: box.y },
    { offset: box.h / 2, val: box.y + box.h / 2 },
    { offset: box.h, val: box.y + box.h },
  ];
  let bestY: { dist: number; pos: number; guide: number } | null = null;
  for (const edge of yEdges) {
    for (const t of yTargets) {
      const dist = Math.abs(edge.val - t);
      if (dist <= THRESHOLD && (!bestY || dist < bestY.dist)) {
        bestY = { dist, pos: proposed.y + (t - edge.val), guide: t };
      }
    }
  }
  if (bestY) {
    y = bestY.pos;
    guides.push({ axis: "y", pos: bestY.guide });
  }

  return { x, y, guides };
}
