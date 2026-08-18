// The printable tape is a fixed 30px tall strip of unbounded width. Every
// coordinate in a label document is in these "tape pixels" (1:1 with what the
// printer receives, before the server-side stretch).
export const TAPE_HEIGHT = 30;

// Physical estimate: ~200 DPI over the 12mm tape → ~0.127mm per tape pixel.
// After the server stretch(2) the horizontal axis doubles.
export const MM_PER_PX = 0.127;

export const PRINTER_MAX_WIDTH = 8000;

export type ElementType = "text" | "icon" | "rect" | "line";

export interface BaseElement {
  id: string;
  type: ElementType;
  x: number;
  y: number;
}

export interface TextElement extends BaseElement {
  type: "text";
  text: string;
  fontFamily: string;
  fontPx: number;
  weight: number;
  italic: boolean;
  letterSpacing: number;
}

export interface IconElement extends BaseElement {
  type: "icon";
  mdiName: string;
  sizePx: number;
}

export interface RectElement extends BaseElement {
  type: "rect";
  w: number;
  h: number;
  lineWidth: number;
  filled: boolean;
}

export interface LineElement extends BaseElement {
  type: "line";
  // A line is defined by its second endpoint relative to (x, y).
  dx: number;
  dy: number;
  lineWidth: number;
}

export type LabelElement = TextElement | IconElement | RectElement | LineElement;

/** The label document: an ordered list of elements plus margins. */
export interface LabelDoc {
  elements: LabelElement[];
  marginLeft: number;
  marginRight: number;
}

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface PrinterInfo {
  name: string;
  mac: string;
}

export interface AppConfig {
  printer_mac: string | null;
  printer_name: string | null;
  default_stretch: number;
  default_dither: boolean;
  fonts: string[];
}

export interface HistoryEntrySummary {
  id: string;
  timestamp: string;
  width: number;
  height: number;
}

export interface HistoryEntryDetail extends HistoryEntrySummary {
  document: LabelDoc;
}
