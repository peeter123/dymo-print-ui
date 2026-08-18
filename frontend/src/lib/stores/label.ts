import { writable, derived, get } from "svelte/store";
import type { LabelElement, TextElement, IconElement, RectElement, LineElement } from "../types";
import { TAPE_HEIGHT } from "../types";

/** The label document: an ordered list of elements plus margins. */
export interface LabelDoc {
  elements: LabelElement[];
  marginLeft: number;
  marginRight: number;
}

const EMPTY: LabelDoc = { elements: [], marginLeft: 8, marginRight: 8 };

export const doc = writable<LabelDoc>(structuredClone(EMPTY));
export const selectedId = writable<string | null>(null);

// ── Undo / redo ──────────────────────────────────────────────────────────────
const past: LabelDoc[] = [];
const future: LabelDoc[] = [];

/** Commit the current doc to history before a mutation. */
function snapshot(): void {
  past.push(structuredClone(get(doc)));
  if (past.length > 100) past.shift();
  future.length = 0;
}

export function undo(): void {
  const prev = past.pop();
  if (!prev) return;
  future.push(structuredClone(get(doc)));
  doc.set(prev);
}

export function redo(): void {
  const next = future.pop();
  if (!next) return;
  past.push(structuredClone(get(doc)));
  doc.set(next);
}

// ── ID generation (no Math.random dependency for determinism in tests) ───────
let idCounter = 0;
function nextId(): string {
  idCounter += 1;
  return `el-${idCounter}-${Date.now().toString(36)}`;
}

// ── Mutations ────────────────────────────────────────────────────────────────

export function addText(partial?: Partial<TextElement>): string {
  snapshot();
  const id = nextId();
  const el: TextElement = {
    id,
    type: "text",
    x: 12,
    y: 6,
    text: "Label",
    fontFamily: "Silkscreen",
    fontPx: 16,
    weight: 400,
    italic: false,
    letterSpacing: 0,
    ...partial,
  };
  doc.update((d) => ({ ...d, elements: [...d.elements, el] }));
  selectedId.set(id);
  return id;
}

export function addIcon(mdiName: string): string {
  snapshot();
  const id = nextId();
  const el: IconElement = {
    id,
    type: "icon",
    x: 12,
    y: 3,
    mdiName,
    sizePx: 24,
  };
  doc.update((d) => ({ ...d, elements: [...d.elements, el] }));
  selectedId.set(id);
  return id;
}

export function addRect(): string {
  snapshot();
  const id = nextId();
  const el: RectElement = {
    id,
    type: "rect",
    x: 12,
    y: 6,
    w: 40,
    h: 18,
    lineWidth: 2,
    filled: false,
  };
  doc.update((d) => ({ ...d, elements: [...d.elements, el] }));
  selectedId.set(id);
  return id;
}

export function addLine(): string {
  snapshot();
  const id = nextId();
  const el: LineElement = {
    id,
    type: "line",
    x: 12,
    y: TAPE_HEIGHT / 2,
    dx: 60,
    dy: 0,
    lineWidth: 2,
  };
  doc.update((d) => ({ ...d, elements: [...d.elements, el] }));
  selectedId.set(id);
  return id;
}

/** Patch an element. Pass `transient` during a drag to skip history spam. */
export function updateElement(
  id: string,
  patch: Partial<LabelElement>,
  transient = false,
): void {
  if (!transient) snapshot();
  doc.update((d) => ({
    ...d,
    elements: d.elements.map((e) => (e.id === id ? ({ ...e, ...patch } as LabelElement) : e)),
  }));
}

/** Begin a drag: take one snapshot, then call updateElement(transient=true). */
export function beginHistory(): void {
  snapshot();
}

export function removeElement(id: string): void {
  snapshot();
  doc.update((d) => ({ ...d, elements: d.elements.filter((e) => e.id !== id) }));
  selectedId.update((s) => (s === id ? null : s));
}

export function bringToFront(id: string): void {
  snapshot();
  doc.update((d) => {
    const el = d.elements.find((e) => e.id === id);
    if (!el) return d;
    return { ...d, elements: [...d.elements.filter((e) => e.id !== id), el] };
  });
}

export function clearAll(): void {
  snapshot();
  doc.set(structuredClone(EMPTY));
  selectedId.set(null);
}

export function setMargins(left: number, right: number): void {
  snapshot();
  doc.update((d) => ({ ...d, marginLeft: left, marginRight: right }));
}

export const selectedElement = derived([doc, selectedId], ([$doc, $id]) =>
  $id ? ($doc.elements.find((e) => e.id === $id) ?? null) : null,
);
