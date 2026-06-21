# CLAUDE.md

Project context for the **dymo-print-ui** label editor. Read this before making
changes.

## What this is

A local, browser-based label editor for the **Dymo LetraTag 200B**. The user
designs a label (text in grid-aligned pixel fonts, Material Design Icons, simple
shapes) in the browser, previews it exactly as it will print, and sends it to the
printer over Bluetooth LE. Everything runs locally on the user's machine.

## Architecture in one breath

A single **FastAPI** process (`src/dymo_print_ui/`) serves a **Svelte + Vite**
SPA (`frontend/`), exposes a JSON `/api/*` surface, bridges to the printer over
BLE via the `dymo_bluetooth` git submodule, and proxy-caches Google Fonts + MDI
icons to disk.

**The browser is the source of truth for pixels.** It renders text/icons/shapes
onto an offscreen `width × 30` canvas, thresholds to 1-bit black/white in JS, and
POSTs a PNG. The backend never re-renders text — it just converts the PNG to a
driver `Canvas`, stretches, and prints. This is what guarantees preview == print.

## Running it

**Dev (two processes):**
```bash
poetry run uvicorn dymo_print_ui.app:app --reload   # backend :8000
cd frontend && npm run dev                          # Vite :5173  ← open this
```
Vite proxies `/api` → `:8000` (see `frontend/vite.config.ts`).

**Production (one process):**
```bash
cd frontend && npm run build      # → frontend/dist/
poetry run dymo-print-ui          # serves SPA + API on :8000, opens browser
```

**Tests:** `poetry run pytest` (the print pipeline; no hardware needed).
**Type check:** `cd frontend && npm run check`.

## The driver (external/dymo-bluetooth submodule)

`dymo_bluetooth` is a git submodule. Poetry 1.7 can't consume its PEP 621
packaging as a path dependency, so it's made importable by prepending its path to
`sys.path` in `src/dymo_print_ui/__init__.py`. Its deps (`bleak`, `pillow`) are
declared directly in `pyproject.toml`. Run `git submodule update --init` after
cloning.

Key API used by `printer_service.py`:
- `discover_printers(max_timeout) -> List[Printer]`; MAC at `printer._impl.address`.
- `Printer(BLEDevice)`, `.connect()/.disconnect()/.print(canvas)` — all async.
  A saved MAC skips discovery: `BleakScanner.find_device_by_address(mac)` → `Printer(dev)`.
- `convert_image_to_canvas(PIL.Image, dither, trim) -> Canvas`; black pixel → filled.
- `Canvas`: **fixed height 30px**, max width 8000px.
- `Result` enum: SUCCESS=0, FAILED=2, SUCCESS_LOW_BATTERY=3, FAILED_CANCEL=4,
  FAILED_LOW_BATTERY=6, FAILED_NO_CASETTE=7.

### Gotchas (these will bite you)
- **Must `canvas.stretch(2)` before printing** or the label prints too narrow.
  Done server-side in `printer_service.build_canvas`; the UI shows length after stretch.
- **`dither=False` is the default here — the OPPOSITE of the driver default.**
  The browser already produces a clean 1-bit image; dithering would diverge from
  the crisp on-screen preview. Set explicitly on every print/preview call.
- **Clamp content to y ∈ [0, 30).** The driver center-crops anything taller than
  30px. The editor keeps the tape height fixed so this never happens.
- **BLE access is exclusive and slow.** All printer ops are serialised through an
  `asyncio.Lock` in `printer_service.py`, and `disconnect()` runs in `finally`.

## Backend layout (src/dymo_print_ui/)

- `app.py` — FastAPI factory; mounts the built SPA with an `index.html` fallback.
- `__main__.py` — `dymo-print-ui` entry point (uvicorn + open browser).
- `config.py` — `ConfigStore`, JSON at `%APPDATA%\dymo-print-ui\config.json`,
  atomic writes. Holds `printer_mac`, defaults, and the font list. Singleton `config`.
  On load it reconciles the font list: ensures `DEFAULT_FONTS` are present, prunes
  `RETIRED_DEFAULT_FONTS` (fonts we shipped before but dropped), and keeps any
  genuinely user-added fonts.
- `printer_service.py` — the BLE + image bridge (build_canvas, list_printers,
  is_reachable, print_canvas, the asyncio.Lock).
- `assets_cache.py` — Google Fonts CSS proxy + woff2 disk cache (rewrites
  `url(...)` → `/api/fonts/file/{hash}.woff2`); MDI icon search (paged via
  `offset`/`limit`) + path data from `frontend/node_modules/@mdi/svg`. Cache lives
  under `user_cache_dir`. `warm_font` tries progressively simpler CSS2 queries
  (`wght@400;700` → `wght@400` → bare family) so single-weight pixel fonts don't
  fail on Google's 400-for-missing-weight behaviour. Two icon endpoints:
  `/api/icons/{name}` returns JSON path data (for canvas `Path2D` rendering — what
  actually prints), `/api/icons/{name}.svg` serves the raw SVG (for `<img>`
  thumbnails in pickers; the JSON route can't be used in `<img>`).
- `routers/` — `printers.py` (`GET /api/printers` scan, `GET /api/printer/status`),
  `printing.py` (`POST /api/print`, `POST /api/print/preview` — same pipeline minus
  BLE, returns the thresholded PNG), `config.py` (`GET/PUT /api/config`,
  `POST /api/config/printer`), `assets.py` (font CSS/file proxy, `GET /api/fonts`
  add/remove, icon search + SVG + path data).

## Frontend layout (frontend/src/)

- `lib/types.ts` — `LabelElement` union (text | icon | rect | line), `TAPE_HEIGHT=30`,
  `MM_PER_PX`, `PRINTER_MAX_WIDTH`.
- `lib/api.ts` — typed fetch wrappers for every endpoint.
- `lib/stores/`
  - `label.ts` — the document (`elements`, margins) + selection + undo/redo +
    mutations (`addText`/`addIcon`/`addRect`/`addLine`, move/delete, etc.). New
    text defaults to **Pixelify Sans 18px / weight 400**.
  - `config.ts` — loads `/api/config`, holds printer + font list defaults.
  - `printerStatus.ts` — shared reachability store (`unknown` / `reachable` /
    `unreachable`), polled on an interval; drives both the nav dot in `App.svelte`
    (grey configured / green in-range / orange out-of-range) and the `PrinterPage`
    badge so they never disagree.
- `lib/render/` — the WYSIWYG pipeline:
  - `draw.ts` — shared element-drawing routine; the **editor display canvas and
    the export canvas both call it**, so they can't drift. **Text is positioned by
    a rounded baseline, not `textBaseline="top"`**: "top" aligns the fractional
    em-box ascent to `el.y`, leaving glyph rows on a sub-pixel offset that smears
    pixel fonts. It draws on `Math.round(el.y + textVMetrics(el).ascent)` so every
    glyph row lands on the tape's pixel grid.
  - `measure.ts` — `textWidth`, `textVMetrics` (font-bounding-box ascent/descent —
    constant per font+size, stable while typing), `textBoxV`/`elementBox`,
    `tapeWidth`, `tapeLengthMm`. **`elementBox` derives a text box from the SAME
    rounded baseline `draw.ts` uses** (`textBoxV`), so the selection outline always
    contains the glyphs (incl. descenders) — a prior mismatch let pixel fonts spill
    past the box.
  - `exportCanvas.ts` — render doc → `width×30` canvas → `thresholdToBinary` → PNG.
    **Edit here if print output looks wrong.** Gates on fonts/icons being loaded first.
  - `fonts.ts` — inject proxied `@font-face`, `ensureFontLoaded` (avoids the
    fallback-font race before rasterising). `injectUiFont()` loads Inter for the
    app chrome separately, since the label font list is pixel-only now.
  - `fontRegistry.ts` — per-font metadata (available weights, grid-locked S/M/L
    sizes). All shipped label fonts are **pixel/bitmap faces** (Pixelify Sans,
    Press Start 2P, Silkscreen, Jersey 10, Tiny5) — proportional fonts were
    dropped because they never thresholded cleanly on the 30px tape. Two jobs:
    (1) `fontQuery` builds the Google CSS2 query requesting only weights the font
    ships — requesting an absent weight makes Google 400 and the font silently
    fails (this is what originally broke pixel fonts); (2) `normalizeForFont` snaps
    size to the font's pixel grid and clamps weight/italic/letter-spacing when you
    switch fonts. The inspector shows S/M/L buttons instead of a free size slider
    for pixel fonts. Unknown (user-added) fonts default to a safe 400-only,
    non-pixel spec. Retired defaults are pruned from existing configs on load
    (`RETIRED_DEFAULT_FONTS` in `config.py`).
  - `icons.ts` — fetch + cache MDI `Path2D`, draw onto canvas.
  - `snapping.ts` — alignment snapping (centre, edges, other elements) + guides.
- `lib/components/`
  - `Editor/` — `Editor.svelte` (shell: toolbar, zoom, pixel-grid toggle,
    fit-to-view), `EditorCanvas.svelte` (interactive tape: drag/select/snap; draws
    a faint per-pixel grid under the elements when `zoom >= 5`; **gates first paint
    on `ensureFontLoaded`/`loadIcon` then redraws**, so a freshly-added element
    never flashes in a fallback face), `LabelPreview.svelte` (full-width 1-bit
    thresholded output strip under the canvas — the exact printer pixels, scaled
    nearest-neighbour), `PrintDialog.svelte`.
  - `Inspector/` — `ElementInspector.svelte` (per-element controls; S/M/L size
    buttons for pixel fonts, free slider otherwise), `FontPicker.svelte`,
    `IconPicker.svelte` (infinite-scroll MDI picker, paged via `/api/icons?offset=`).
  - `Settings/` — `PrinterPage.svelte` (scan/select/manual MAC/status badge),
    `FontManager.svelte` (add/remove Google Fonts).
- There is **no Quick-label mode** anymore — it was removed; the single Design
  surface (toolbar `＋ Text`/`＋ Icon`/`＋ Box`/`＋ Line`) covers everything.

## Pixel fonts (why this app is fussy about text)

Label text uses **pixel/bitmap fonts only** (Pixelify Sans, Press Start 2P,
Silkscreen, Jersey 10, Tiny5). They render dead-sharp through the 1-bit threshold
— but only when two things hold, both enforced in code:

1. **Size is a grid multiple.** Each font has S/M/L `gridSizes` in
   `fontRegistry.ts`; the inspector exposes only those for pixel fonts, and
   `normalizeForFont` snaps size + zeroes letter-spacing when you pick the font.
2. **The baseline is integer-aligned.** `draw.ts` rounds `el.y + ascent` before
   drawing, and `measure.ts` builds the selection box from that same rounded
   baseline. If you change one, change the other or glyphs will smear / spill the
   box. (If a specific font still looks a pixel off at a size, tune its
   `gridSizes`.)

`Inter` is loaded only for the app's own UI chrome (`injectUiFont`), not as a
label font.

## Design language

Editorial / paper: warm off-white background, ink-near-black text, one muted
vermilion accent (`--accent`), Inter for UI, hairline rules, restrained shadows,
the white tape strip as the centrepiece. The whole system lives in
`frontend/src/styles/global.css` (CSS custom properties) — keep additions in that
vocabulary; avoid gradients-for-their-own-sake and the generic card-grid dashboard
look.

## Verifying without a printer

- `poetry run pytest` covers `build_canvas` (convert → stretch → pad, black→filled).
- `POST /api/print/preview` runs the exact print pipeline minus BLE and returns
  the post-threshold PNG, so you can confirm preview == print output.
- Discovery / real printing (`GET /api/printers`, `POST /api/print`) need the
  LetraTag powered and awake.
