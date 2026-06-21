<script lang="ts">
  import { doc } from "../../stores/label";
  import { config } from "../../stores/config";
  import { api } from "../../api";
  import { renderToPng } from "../../render/exportCanvas";
  import { tapeWidth, tapeLengthMm } from "../../render/measure";
  import { PRINTER_MAX_WIDTH } from "../../types";

  interface Props {
    onClose: () => void;
    onGoToSettings: () => void;
  }
  let { onClose, onGoToSettings }: Props = $props();

  let copies = $state(1);
  let printing = $state(false);
  let result = $state<{ ok: boolean; message: string } | null>(null);

  const stretch = $derived($config.default_stretch ?? 2);
  const width = $derived(tapeWidth($doc.elements, $doc.marginLeft, $doc.marginRight));
  const stretchedWidth = $derived(width * stretch);
  const lengthMm = $derived(tapeLengthMm(width, stretch));
  const tooWide = $derived(stretchedWidth > PRINTER_MAX_WIDTH);
  const hasPrinter = $derived(!!$config.printer_mac);

  async function print(): Promise<void> {
    printing = true;
    result = null;
    try {
      const png = await renderToPng($doc);
      const res = await api.print(png, {
        copies,
        stretch,
        dither: $config.default_dither ?? false,
        padding: 0,
      });
      const ok = res.result.startsWith("SUCCESS");
      let message = ok ? "Printed successfully." : `Printer reported: ${res.result}`;
      if (res.low_battery) message += " (battery low)";
      result = { ok, message };
    } catch (e) {
      result = { ok: false, message: e instanceof Error ? e.message : "Print failed" };
    }
    printing = false;
  }
</script>

<div class="overlay" role="presentation" onclick={(e) => e.target === e.currentTarget && onClose()}>
  <div class="dialog" role="dialog" aria-label="Print label">
    <header><span class="eyebrow">Print</span><h2>Send to printer</h2></header>

    <dl class="stats">
      <div><dt>Tape length</dt><dd>≈ {lengthMm.toFixed(0)} mm</dd></div>
      <div><dt>Resolution</dt><dd>{stretchedWidth} × 30 px</dd></div>
    </dl>

    {#if tooWide}
      <p class="warn">This label exceeds the printer's maximum width. Shorten it before printing.</p>
    {/if}

    {#if !hasPrinter}
      <p class="warn">
        No printer configured. The app will scan on print, or you can
        <button class="link" onclick={onGoToSettings}>set one up</button>.
      </p>
    {/if}

    <div class="field copies">
      <label for="copies">Copies</label>
      <input id="copies" type="number" class="input" min="1" max="20" bind:value={copies} />
    </div>

    {#if result}
      <div class="result" class:ok={result.ok} class:bad={!result.ok}>{result.message}</div>
    {/if}

    <footer>
      <button class="btn btn-ghost" onclick={onClose}>Close</button>
      <button class="btn btn-primary" disabled={printing || tooWide} onclick={print}>
        {printing ? "Printing…" : "Print"}
      </button>
    </footer>
  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(28, 26, 23, 0.32);
    display: grid;
    place-items: center;
    z-index: 50;
  }

  .dialog {
    width: min(420px, 92vw);
    background: var(--paper-raised);
    border: 1px solid var(--rule-strong);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow);
    padding: 22px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  h2 {
    margin-top: 3px;
    font-size: 19px;
  }

  .stats {
    display: flex;
    gap: 12px;
    margin: 0;
  }

  .stats > div {
    flex: 1;
    padding: 12px 14px;
    background: #fff;
    border: 1px solid var(--rule);
    border-radius: var(--radius);
  }

  dt {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--ink-faint);
  }

  dd {
    margin: 4px 0 0;
    font-weight: 600;
    font-size: 17px;
  }

  .copies {
    max-width: 120px;
  }

  .warn {
    margin: 0;
    padding: 10px 12px;
    background: var(--accent-wash);
    border-radius: var(--radius);
    font-size: 13px;
    color: #8a3320;
  }

  .link {
    border: none;
    background: none;
    color: var(--accent);
    text-decoration: underline;
    cursor: pointer;
    padding: 0;
    font: inherit;
  }

  .result {
    padding: 10px 12px;
    border-radius: var(--radius);
    font-size: 14px;
  }

  .result.ok {
    background: #e7f0e9;
    color: #2f6440;
  }

  .result.bad {
    background: var(--accent-wash);
    color: #8a3320;
  }

  footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }
</style>
