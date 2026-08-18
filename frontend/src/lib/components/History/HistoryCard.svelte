<script lang="ts">
  import type { HistoryEntrySummary } from "../../types";
  import { api } from "../../api";

  interface Props {
    entry: HistoryEntrySummary;
    onRestore: () => void;
    onDeleted: () => void;
  }
  let { entry, onRestore, onDeleted }: Props = $props();

  let copies = $state(1);
  let reprinting = $state(false);
  let result = $state<{ ok: boolean; message: string } | null>(null);

  const timestamp = $derived(new Date(entry.timestamp).toLocaleString());

  async function reprint(): Promise<void> {
    reprinting = true;
    result = null;
    try {
      const res = await api.reprintHistoryEntry(entry.id, copies);
      const ok = res.result.startsWith("SUCCESS");
      let message = ok ? "Reprinted successfully." : `Printer reported: ${res.result}`;
      if (res.low_battery) message += " (battery low)";
      result = { ok, message };
    } catch (e) {
      result = { ok: false, message: e instanceof Error ? e.message : "Reprint failed" };
    }
    reprinting = false;
  }

  async function del(): Promise<void> {
    await api.deleteHistoryEntry(entry.id);
    onDeleted();
  }
</script>

<li class="card">
  <img
    class="thumb"
    src={`/api/history/${entry.id}/thumbnail.png`}
    alt="Printed label from {timestamp}"
  />

  <div class="info">
    <div class="timestamp">{timestamp}</div>
    <div class="dims">{entry.width} × {entry.height} px</div>
    {#if result}
      <div class="result" class:ok={result.ok} class:bad={!result.ok}>{result.message}</div>
    {/if}
  </div>

  <div class="actions">
    <button class="btn btn-ghost" onclick={onRestore}>Restore to editor</button>
    <div class="reprint">
      <input
        class="input copies"
        type="number"
        min="1"
        max="20"
        bind:value={copies}
        aria-label="Copies"
      />
      <button class="btn" disabled={reprinting} onclick={reprint}>
        {reprinting ? "Printing…" : "Reprint"}
      </button>
    </div>
    <button class="btn btn-ghost" onclick={del}>Delete</button>
  </div>
</li>

<style>
  .card {
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 14px 16px;
    background: var(--paper-raised);
  }

  .card:not(:last-child) {
    border-bottom: 1px solid var(--rule);
  }

  .thumb {
    flex-shrink: 0;
    height: 30px;
    max-width: 220px;
    width: auto;
    object-fit: contain;
    background: #fff;
    border: 1px solid var(--rule);
    border-radius: 3px;
    image-rendering: pixelated;
  }

  .info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .timestamp {
    font-weight: 600;
    font-size: 14px;
  }

  .dims {
    font-size: 12px;
    color: var(--ink-faint);
    font-family: var(--font-mono);
  }

  .result {
    font-size: 12px;
    margin-top: 2px;
  }

  .result.ok {
    color: #2f6440;
  }

  .result.bad {
    color: #8a3320;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .reprint {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .copies {
    width: 52px;
  }
</style>
