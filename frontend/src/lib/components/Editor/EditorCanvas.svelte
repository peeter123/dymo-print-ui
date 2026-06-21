<script lang="ts">
  import { onMount } from "svelte";
  import { doc, selectedId, beginHistory, updateElement } from "../../stores/label";
  import type { LabelElement } from "../../types";
  import { TAPE_HEIGHT } from "../../types";
  import { drawElements } from "../../render/draw";
  import { elementBox, tapeWidth } from "../../render/measure";
  import { snapPosition, type Guide } from "../../render/snapping";
  import { loadIcon } from "../../render/icons";
  import { ensureFontLoaded } from "../../render/fonts";

  interface Props {
    zoom: number;
    showGrid?: boolean;
  }
  let { zoom, showGrid = true }: Props = $props();

  let canvasEl: HTMLCanvasElement;
  let wrapEl: HTMLDivElement;
  let guides = $state<Guide[]>([]);

  const width = $derived(tapeWidth($doc.elements, $doc.marginLeft, $doc.marginRight));

  // Redraw whenever the doc, selection, zoom or width change.
  $effect(() => {
    // touch reactive deps
    $doc;
    $selectedId;
    zoom;
    width;
    showGrid;
    void redraw();
  });

  // Ensure assets are loaded so they render correctly on first paint. Text fonts
  // (now pixel fonts) and icons both load async; without this the first render
  // of a freshly-added element falls back to the wrong face/blank box.
  $effect(() => {
    for (const el of $doc.elements) {
      if (el.type === "icon") {
        void loadIcon(el.mdiName).then(() => redraw());
      } else if (el.type === "text") {
        void ensureFontLoaded(el.fontFamily, el.weight, el.italic).then(() => redraw());
      }
    }
  });

  async function redraw(): Promise<void> {
    if (!canvasEl) return;
    const dpr = window.devicePixelRatio || 1;
    canvasEl.width = Math.max(1, Math.round(width * zoom * dpr));
    canvasEl.height = Math.round(TAPE_HEIGHT * zoom * dpr);
    const ctx = canvasEl.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingEnabled = false;

    // White tape
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, width * zoom, TAPE_HEIGHT * zoom);

    // Pixel grid — one cell per tape pixel. Only worth drawing when zoomed in
    // enough that the lines don't merge into grey. Drawn under the elements.
    if (showGrid && zoom >= 5) {
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let x = 0; x <= width; x++) {
        const px = Math.round(x * zoom) + 0.5;
        ctx.moveTo(px, 0);
        ctx.lineTo(px, TAPE_HEIGHT * zoom);
      }
      for (let y = 0; y <= TAPE_HEIGHT; y++) {
        const py = Math.round(y * zoom) + 0.5;
        ctx.moveTo(0, py);
        ctx.lineTo(width * zoom, py);
      }
      ctx.strokeStyle = "rgba(28, 26, 23, 0.07)";
      ctx.stroke();
    }

    ctx.save();
    ctx.scale(zoom, zoom);
    ctx.translate($doc.marginLeft, 0);
    drawElements(ctx, $doc.elements);
    ctx.restore();
  }

  // ── Hit testing & dragging ────────────────────────────────────────────────
  interface DragState {
    id: string;
    startX: number;
    startY: number;
    origX: number;
    origY: number;
  }
  let drag: DragState | null = null;

  function toTapeCoords(e: PointerEvent): { x: number; y: number } {
    const rect = wrapEl.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) / zoom - $doc.marginLeft,
      y: (e.clientY - rect.top) / zoom,
    };
  }

  function hitTest(x: number, y: number): LabelElement | null {
    // Topmost first (elements drawn last are on top).
    for (let i = $doc.elements.length - 1; i >= 0; i--) {
      const el = $doc.elements[i];
      const b = elementBox(el);
      const pad = 3; // generous grab area for thin elements
      if (x >= b.x - pad && x <= b.x + b.w + pad && y >= b.y - pad && y <= b.y + b.h + pad) {
        return el;
      }
    }
    return null;
  }

  function onPointerDown(e: PointerEvent): void {
    const { x, y } = toTapeCoords(e);
    const hit = hitTest(x, y);
    if (hit) {
      selectedId.set(hit.id);
      beginHistory();
      drag = { id: hit.id, startX: x, startY: y, origX: hit.x, origY: hit.y };
      canvasEl.setPointerCapture(e.pointerId);
    } else {
      selectedId.set(null);
    }
  }

  function onPointerMove(e: PointerEvent): void {
    if (!drag) return;
    const { x, y } = toTapeCoords(e);
    const el = $doc.elements.find((d) => d.id === drag!.id);
    if (!el) return;
    const proposed = {
      x: Math.round(drag.origX + (x - drag.startX)),
      y: Math.round(drag.origY + (y - drag.startY)),
    };
    const others = $doc.elements.filter((d) => d.id !== drag!.id);
    const snapped = e.shiftKey
      ? { x: proposed.x, y: proposed.y, guides: [] }
      : snapPosition(el, others, proposed);
    guides = snapped.guides;
    updateElement(drag.id, { x: snapped.x, y: snapped.y }, true);
  }

  function onPointerUp(e: PointerEvent): void {
    if (drag) {
      canvasEl.releasePointerCapture(e.pointerId);
      drag = null;
      guides = [];
    }
  }

  const selBox = $derived.by(() => {
    const el = $doc.elements.find((d) => d.id === $selectedId);
    if (!el) return null;
    const b = elementBox(el);
    return b;
  });
</script>

<div class="canvas-wrap" bind:this={wrapEl} style="height: {TAPE_HEIGHT * zoom}px">
  <canvas
    bind:this={canvasEl}
    style="width: {width * zoom}px; height: {TAPE_HEIGHT * zoom}px"
    onpointerdown={onPointerDown}
    onpointermove={onPointerMove}
    onpointerup={onPointerUp}
  ></canvas>

  <!-- Selection outline -->
  {#if selBox}
    <div
      class="sel"
      style="
        left: {($doc.marginLeft + selBox.x) * zoom}px;
        top: {selBox.y * zoom}px;
        width: {selBox.w * zoom}px;
        height: {selBox.h * zoom}px;"
    ></div>
  {/if}

  <!-- Alignment guides -->
  {#each guides as g}
    {#if g.axis === "x"}
      <div class="guide guide-v" style="left: {($doc.marginLeft + g.pos) * zoom}px"></div>
    {:else}
      <div class="guide guide-h" style="top: {g.pos * zoom}px"></div>
    {/if}
  {/each}
</div>

<style>
  .canvas-wrap {
    position: relative;
    display: inline-block;
    /* The tape itself: a crisp white strip with rounded ends and a real shadow. */
    background: #fff;
    border-radius: 5px;
    box-shadow:
      0 1px 0 rgba(0, 0, 0, 0.04),
      0 10px 30px rgba(28, 26, 23, 0.12);
    outline: 1px solid var(--rule);
  }

  canvas {
    display: block;
    border-radius: 5px;
    touch-action: none;
    cursor: default;
  }

  .sel {
    position: absolute;
    border: 1px solid var(--accent);
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.6);
    pointer-events: none;
    border-radius: 1px;
  }

  .guide {
    position: absolute;
    background: var(--accent);
    pointer-events: none;
    opacity: 0.8;
  }

  .guide-v {
    top: -6px;
    bottom: -6px;
    width: 1px;
  }

  .guide-h {
    left: -6px;
    right: -6px;
    height: 1px;
  }
</style>
