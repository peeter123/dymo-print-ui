<script lang="ts">
  import {
    doc,
    selectedId,
    addText,
    addIcon,
    addRect,
    addLine,
    removeElement,
    clearAll,
    undo,
    redo,
  } from "../../stores/label";
  import { config } from "../../stores/config";
  import { tapeWidth, tapeLengthMm } from "../../render/measure";
  import { renderToPng } from "../../render/exportCanvas";
  import { api } from "../../api";
  import EditorCanvas from "./EditorCanvas.svelte";
  import ElementInspector from "../Inspector/ElementInspector.svelte";
  import IconPicker from "../Inspector/IconPicker.svelte";
  import PrintDialog from "./PrintDialog.svelte";
  import LabelPreview from "./LabelPreview.svelte";

  interface Props {
    onGoToSettings: () => void;
  }
  let { onGoToSettings }: Props = $props();

  let zoom = $state(10);
  let showIconPicker = $state(false);
  let showPrint = $state(false);
  let showGrid = $state(true);
  let stageWidth = $state(0);
  let savingDraft = $state(false);
  let draftSaved = $state(false);

  const width = $derived(tapeWidth($doc.elements, $doc.marginLeft, $doc.marginRight));
  const stretch = $derived($config.default_stretch ?? 2);
  const lengthMm = $derived(tapeLengthMm(width, stretch));

  /** Fit the editing canvas to the available stage width (clamped 3–16×). */
  function fitZoom(): void {
    if (stageWidth === 0 || width === 0) return;
    const fit = Math.floor((stageWidth - 24) / width);
    zoom = Math.max(3, Math.min(16, fit || 3));
  }

  function onKeydown(e: KeyboardEvent): void {
    const target = e.target as HTMLElement;
    if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT")
      return;
    if ((e.key === "Delete" || e.key === "Backspace") && $selectedId) {
      e.preventDefault();
      removeElement($selectedId);
    } else if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) {
      e.preventDefault();
      undo();
    } else if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.shiftKey && e.key === "z"))) {
      e.preventDefault();
      redo();
    }
  }

  async function saveDraft(): Promise<void> {
    savingDraft = true;
    draftSaved = false;
    try {
      const png = await renderToPng($doc);
      await api.saveHistoryDraft(png, $doc, {
        stretch: $config.default_stretch ?? 2,
        dither: $config.default_dither ?? false,
        padding: 0,
      });
      draftSaved = true;
      setTimeout(() => (draftSaved = false), 2000);
    } catch (e) {
      console.error("Failed to save to history", e);
    }
    savingDraft = false;
  }
</script>

<svelte:window onkeydown={onKeydown} />

<div class="editor">
  <!-- Toolbar -->
  <div class="toolbar">
    <div class="tools">
      <button class="btn" onclick={() => addText()}>＋ Text</button>
      <button class="btn" onclick={() => (showIconPicker = true)}>＋ Icon</button>
      <button class="btn" onclick={() => addRect()}>＋ Box</button>
      <button class="btn" onclick={() => addLine()}>＋ Line</button>
      <span class="sep"></span>
      <button class="btn btn-ghost btn-icon" title="Undo (Ctrl+Z)" onclick={undo}>↶</button>
      <button class="btn btn-ghost btn-icon" title="Redo (Ctrl+Y)" onclick={redo}>↷</button>
      <button class="btn btn-ghost" onclick={clearAll}>Clear</button>
    </div>

    <div class="right">
      {#if draftSaved}<span class="draft-saved">Saved to history</span>{/if}
      <button class="btn btn-ghost" disabled={savingDraft} onclick={saveDraft}>
        {savingDraft ? "Saving…" : "Save to History"}
      </button>
      <button class="btn btn-primary" onclick={() => (showPrint = true)}>Print…</button>
    </div>
  </div>

  <div class="workspace">
    <!-- Stage with the tape + the full-width output preview below it -->
    <div class="main-col">
      <div class="stage" bind:clientWidth={stageWidth}>
        <div class="stage-inner">
          <div class="ruler">
            <span>{width}px · ≈ {lengthMm.toFixed(0)} mm</span>
            <div class="ruler-controls">
              <button
                class="btn btn-ghost grid-toggle"
                class:on={showGrid}
                title="Toggle pixel grid"
                onclick={() => (showGrid = !showGrid)}>▦ Grid</button
              >
              <button class="btn btn-ghost grid-toggle" title="Fit label to view" onclick={fitZoom}>⤢ Fit</button>
              <div class="zoom">
                <button class="btn btn-ghost btn-icon" onclick={() => (zoom = Math.max(3, zoom - 1))}>−</button>
                <span class="zoom-val">{zoom}×</span>
                <button class="btn btn-ghost btn-icon" onclick={() => (zoom = Math.min(16, zoom + 1))}>＋</button>
              </div>
            </div>
          </div>
          <div class="tape-scroll">
            <EditorCanvas {zoom} {showGrid} />
          </div>
        </div>
      </div>

      <LabelPreview />
    </div>

    <!-- Inspector -->
    <aside class="panel">
      <ElementInspector />
    </aside>
  </div>
</div>

{#if showIconPicker}
  <IconPicker
    onPick={(name) => {
      addIcon(name);
      showIconPicker = false;
    }}
    onClose={() => (showIconPicker = false)}
  />
{/if}

{#if showPrint}
  <PrintDialog onClose={() => (showPrint = false)} {onGoToSettings} />
{/if}

<style>
  .editor {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .toolbar {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 22px;
    border-bottom: 1px solid var(--rule);
    background: var(--paper-raised);
  }

  .tools {
    display: flex;
    align-items: center;
    gap: 7px;
  }

  .sep {
    width: 1px;
    height: 22px;
    background: var(--rule);
    margin: 0 4px;
  }

  .right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .draft-saved {
    font-size: 12px;
    color: #2f6440;
  }

  .workspace {
    flex: 1;
    min-height: 0;
    display: grid;
    grid-template-columns: 1fr 300px;
  }

  .main-col {
    display: flex;
    flex-direction: column;
    min-width: 0;
    min-height: 0;
  }

  .stage {
    flex: 1;
    min-height: 0;
    overflow: auto;
    display: grid;
    place-items: center;
    padding: 40px;
    background:
      radial-gradient(circle at center, rgba(28, 26, 23, 0.02), transparent 70%);
  }

  .stage-inner {
    display: flex;
    flex-direction: column;
    gap: 14px;
    max-width: 100%;
  }

  .ruler {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    color: var(--ink-faint);
    font-family: var(--font-mono);
  }

  .zoom {
    display: flex;
    align-items: center;
    gap: 2px;
  }

  .ruler-controls {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .grid-toggle {
    font-size: 12px;
    padding: 4px 9px;
    color: var(--ink-faint);
  }

  .grid-toggle.on {
    color: var(--ink);
    background: rgba(28, 26, 23, 0.06);
  }

  .zoom-val {
    min-width: 30px;
    text-align: center;
  }

  .tape-scroll {
    overflow-x: auto;
    padding: 6px;
    max-width: 100%;
  }

  .panel {
    border-left: 1px solid var(--rule);
    padding: 20px;
    overflow-y: auto;
    background: var(--paper-raised);
  }
</style>
