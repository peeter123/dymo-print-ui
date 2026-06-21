<script lang="ts">
  import { doc } from "../../stores/label";
  import { renderExportCanvas } from "../../render/exportCanvas";
  import { tapeWidth, tapeLengthMm } from "../../render/measure";
  import { config } from "../../stores/config";

  // Shows the authoritative 1-bit output — the exact pixels the printer
  // receives — scaled up with nearest-neighbour so font rasterisation and pixel
  // alignment are visible. Auto-fits the whole label to the available width;
  // very wide labels stay at the minimum scale and scroll horizontally.
  let host = $state<HTMLDivElement>();
  let canvasEl = $state<HTMLCanvasElement>();
  let hostWidth = $state(0);

  const width = $derived(tapeWidth($doc.elements, $doc.marginLeft, $doc.marginRight));
  const stretch = $derived($config.default_stretch ?? 2);
  const lengthMm = $derived(tapeLengthMm(width, stretch));

  let scale = $state(1);

  $effect(() => {
    // redraw on any of these
    $doc;
    hostWidth;
    void render();
  });

  async function render(): Promise<void> {
    if (!canvasEl || hostWidth === 0) return;
    const src = await renderExportCanvas($doc); // width×30, thresholded to 1-bit

    // Largest integer scale that still fits the host width, clamped so short
    // labels don't balloon and tall renders stay reasonable.
    const fit = Math.floor((hostWidth - 2) / src.width);
    scale = Math.max(1, Math.min(6, fit || 1));

    const dpr = window.devicePixelRatio || 1;
    canvasEl.width = Math.round(src.width * scale * dpr);
    canvasEl.height = Math.round(src.height * scale * dpr);
    canvasEl.style.width = `${src.width * scale}px`;
    canvasEl.style.height = `${src.height * scale}px`;
    const ctx = canvasEl.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(src, 0, 0, src.width * scale, src.height * scale);
  }
</script>

<div class="preview-panel">
  <div class="preview-head">
    <span class="eyebrow">Output preview</span>
    <span class="meta">actual pixels · {width} × 30 · {scale}×</span>
  </div>
  <div class="preview-scroll" bind:this={host} bind:clientWidth={hostWidth}>
    <canvas bind:this={canvasEl}></canvas>
  </div>
</div>

<style>
  .preview-panel {
    border-top: 1px solid var(--rule);
    background: var(--paper-raised);
    padding: 12px 22px 16px;
    display: flex;
    flex-direction: column;
    gap: 9px;
  }

  .preview-head {
    display: flex;
    align-items: baseline;
    gap: 12px;
  }

  .meta {
    font-size: 11px;
    color: var(--ink-faint);
    font-family: var(--font-mono);
  }

  .preview-scroll {
    overflow-x: auto;
    overflow-y: hidden;
    display: flex;
    justify-content: flex-start;
  }

  canvas {
    display: block;
    background: #fff;
    border-radius: 3px;
    outline: 1px solid var(--rule);
    /* Keep pixels crisp when the browser composites the already-scaled canvas. */
    image-rendering: pixelated;
  }
</style>
