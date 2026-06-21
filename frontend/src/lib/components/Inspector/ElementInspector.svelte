<script lang="ts">
  import { selectedElement, updateElement, removeElement, bringToFront } from "../../stores/label";
  import type { TextElement, IconElement, RectElement, LineElement } from "../../types";
  import { getFontSpec, normalizeForFont } from "../../render/fontRegistry";
  import FontPicker from "./FontPicker.svelte";
  import IconPicker from "./IconPicker.svelte";

  let showIconPicker = $state(false);

  const el = $derived($selectedElement);

  function patch(p: Record<string, unknown>): void {
    if (el) updateElement(el.id, p as any);
  }

  /** Change font and snap weight/italic/size to what the new font supports. */
  function changeFont(family: string): void {
    if (!el || el.type !== "text") return;
    const spec = getFontSpec(family);
    const fixups = normalizeForFont({ ...(el as TextElement), fontFamily: family }, spec);
    patch({ fontFamily: family, ...fixups });
  }

  const spec = $derived(el?.type === "text" ? getFontSpec((el as TextElement).fontFamily) : null);
  const sizeLabels = ["S", "M", "L"];
</script>

{#if !el}
  <div class="empty">
    <p class="eyebrow">No selection</p>
    <p class="hint">Select an element on the tape to edit it, or add one from the toolbar.</p>
  </div>
{:else}
  <div class="inspector">
    <header class="head">
      <span class="eyebrow">{el.type}</span>
      <div class="head-actions">
        <button class="btn btn-ghost btn-icon" title="Bring to front" onclick={() => bringToFront(el.id)}>⤒</button>
        <button class="btn btn-ghost btn-icon danger" title="Delete" onclick={() => removeElement(el.id)}>✕</button>
      </div>
    </header>

    {#if el.type === "text"}
      {@const t = el as TextElement}
      <div class="field">
        <label for="txt">Text</label>
        <input id="txt" class="input" value={t.text} oninput={(e) => patch({ text: (e.currentTarget as HTMLInputElement).value })} />
      </div>

      <div class="field">
        <span class="lbl">Font</span>
        <FontPicker value={t.fontFamily} onChange={changeFont} />
      </div>

      {#if spec?.pixel && spec.gridSizes}
        <div class="field">
          <span class="lbl">Size — grid-locked ({t.fontPx}px)</span>
          <div class="seg-group">
            {#each spec.gridSizes as gs, i}
              <button
                class="seg-btn"
                class:on={t.fontPx === gs}
                onclick={() => patch({ fontPx: gs })}
              >
                {sizeLabels[i]}<span class="seg-sub">{gs}px</span>
              </button>
            {/each}
          </div>
        </div>
      {:else}
        <div class="row">
          <div class="field">
            <label for="size">Size ({t.fontPx}px)</label>
            <input id="size" type="range" min="6" max="30" value={t.fontPx} oninput={(e) => patch({ fontPx: +(e.currentTarget as HTMLInputElement).value })} />
          </div>
        </div>
      {/if}

      <div class="row">
        <div class="field">
          <label for="wt">Weight</label>
          <select id="wt" class="select" value={t.weight} onchange={(e) => patch({ weight: +(e.currentTarget as HTMLSelectElement).value })}>
            {#each spec?.weights ?? [400] as w}
              <option value={w}>{w}</option>
            {/each}
          </select>
        </div>
        {#if spec?.italic}
          <div class="field narrow">
            <label for="it">Italic</label>
            <input id="it" type="checkbox" checked={t.italic} onchange={(e) => patch({ italic: (e.currentTarget as HTMLInputElement).checked })} />
          </div>
        {/if}
      </div>

      {#if !spec?.pixel}
        <div class="field">
          <label for="ls">Letter spacing ({t.letterSpacing})</label>
          <input id="ls" type="range" min="-2" max="10" step="0.5" value={t.letterSpacing} oninput={(e) => patch({ letterSpacing: +(e.currentTarget as HTMLInputElement).value })} />
        </div>
      {/if}
    {:else if el.type === "icon"}
      {@const ic = el as IconElement}
      <div class="field">
        <span class="lbl">Icon</span>
        <button class="btn icon-choose" onclick={() => (showIconPicker = true)}>
          <img src={`/api/icons/${ic.mdiName}.svg`} alt={ic.mdiName} class="mini" />
          <span>{ic.mdiName}</span>
        </button>
      </div>
      <div class="field">
        <label for="isz">Size ({ic.sizePx}px)</label>
        <input id="isz" type="range" min="8" max="30" value={ic.sizePx} oninput={(e) => patch({ sizePx: +(e.currentTarget as HTMLInputElement).value })} />
      </div>
    {:else if el.type === "rect"}
      {@const r = el as RectElement}
      <div class="row">
        <div class="field"><label for="rw">Width</label><input id="rw" type="number" class="input" value={r.w} oninput={(e) => patch({ w: +(e.currentTarget as HTMLInputElement).value })} /></div>
        <div class="field"><label for="rh">Height</label><input id="rh" type="number" class="input" value={r.h} oninput={(e) => patch({ h: +(e.currentTarget as HTMLInputElement).value })} /></div>
      </div>
      <div class="row">
        <div class="field"><label for="rl">Stroke</label><input id="rl" type="number" class="input" min="1" max="10" value={r.lineWidth} oninput={(e) => patch({ lineWidth: +(e.currentTarget as HTMLInputElement).value })} /></div>
        <div class="field narrow"><label for="rf">Filled</label><input id="rf" type="checkbox" checked={r.filled} onchange={(e) => patch({ filled: (e.currentTarget as HTMLInputElement).checked })} /></div>
      </div>
    {:else if el.type === "line"}
      {@const ln = el as LineElement}
      <div class="row">
        <div class="field"><label for="ldx">Length X</label><input id="ldx" type="number" class="input" value={ln.dx} oninput={(e) => patch({ dx: +(e.currentTarget as HTMLInputElement).value })} /></div>
        <div class="field"><label for="ldy">Length Y</label><input id="ldy" type="number" class="input" value={ln.dy} oninput={(e) => patch({ dy: +(e.currentTarget as HTMLInputElement).value })} /></div>
      </div>
      <div class="field"><label for="lw">Thickness</label><input id="lw" type="number" class="input" min="1" max="12" value={ln.lineWidth} oninput={(e) => patch({ lineWidth: +(e.currentTarget as HTMLInputElement).value })} /></div>
    {/if}

    <div class="row pos">
      <div class="field"><label for="px">X</label><input id="px" type="number" class="input" value={Math.round(el.x)} oninput={(e) => patch({ x: +(e.currentTarget as HTMLInputElement).value })} /></div>
      <div class="field"><label for="py">Y</label><input id="py" type="number" class="input" value={Math.round(el.y)} oninput={(e) => patch({ y: +(e.currentTarget as HTMLInputElement).value })} /></div>
    </div>
  </div>
{/if}

{#if showIconPicker && el?.type === "icon"}
  <IconPicker
    onPick={(name) => {
      patch({ mdiName: name });
      showIconPicker = false;
    }}
    onClose={() => (showIconPicker = false)}
  />
{/if}

<style>
  .inspector {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .seg-group {
    display: flex;
    gap: 6px;
  }

  .seg-btn {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    padding: 8px 4px;
    border: 1px solid var(--rule-strong);
    border-radius: var(--radius);
    background: var(--paper-raised);
    color: var(--ink-soft);
    font-weight: 600;
    cursor: pointer;
  }

  .seg-btn:hover {
    border-color: var(--ink-soft);
  }

  .seg-btn.on {
    border-color: var(--accent);
    background: var(--accent-wash);
    color: var(--ink);
  }

  .seg-sub {
    font-size: 10px;
    font-weight: 500;
    color: var(--ink-faint);
    font-family: var(--font-mono);
  }

  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--rule);
  }

  .head-actions {
    display: flex;
    gap: 2px;
  }

  .danger:hover {
    color: var(--accent);
  }

  .row {
    display: flex;
    gap: 10px;
  }

  .row .field {
    flex: 1;
  }

  .field.narrow {
    flex: 0 0 auto;
    align-items: flex-start;
  }

  .pos {
    margin-top: 4px;
    padding-top: 12px;
    border-top: 1px solid var(--rule);
  }

  input[type="range"] {
    width: 100%;
    accent-color: var(--accent);
  }

  input[type="checkbox"] {
    width: 16px;
    height: 16px;
    accent-color: var(--accent);
  }

  .icon-choose {
    justify-content: flex-start;
    width: 100%;
  }

  .mini {
    width: 18px;
    height: 18px;
  }

  .empty {
    color: var(--ink-faint);
  }

  .empty .hint {
    font-size: 13px;
    margin-top: 6px;
    line-height: 1.5;
  }
</style>
