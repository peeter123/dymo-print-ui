<script lang="ts">
  import { onMount } from "svelte";
  import { api } from "../../api";
  import { loadDocument } from "../../stores/label";
  import type { HistoryEntrySummary } from "../../types";
  import HistoryCard from "./HistoryCard.svelte";

  interface Props {
    onGoToEditor: () => void;
  }
  let { onGoToEditor }: Props = $props();

  let entries = $state<HistoryEntrySummary[]>([]);
  let loading = $state(true);
  let error = $state("");

  onMount(load);

  async function load(): Promise<void> {
    loading = true;
    error = "";
    try {
      entries = await api.getHistory();
    } catch (e) {
      error = e instanceof Error ? e.message : "Could not load history";
    }
    loading = false;
  }

  async function restore(id: string): Promise<void> {
    const entry = await api.getHistoryEntry(id);
    loadDocument(entry.document);
    onGoToEditor();
  }

  function removed(id: string): void {
    entries = entries.filter((e) => e.id !== id);
  }
</script>

<div class="page">
  <section class="block">
    <header class="block-head">
      <span class="eyebrow">History</span>
      <h2>Printed labels</h2>
    </header>

    {#if loading}
      <p class="muted">Loading…</p>
    {:else if error}
      <p class="err">{error}</p>
    {:else if entries.length === 0}
      <p class="muted">No prints yet. Labels you print — or save — will appear here.</p>
    {:else}
      <ul class="list">
        {#each entries as entry (entry.id)}
          <HistoryCard {entry} onRestore={() => restore(entry.id)} onDeleted={() => removed(entry.id)} />
        {/each}
      </ul>
    {/if}
  </section>
</div>

<style>
  .page {
    max-width: 880px;
    margin: 0 auto;
    padding: 40px 24px 80px;
  }

  .block-head {
    margin-bottom: 18px;
  }

  .block-head h2 {
    margin-top: 4px;
    font-size: 22px;
  }

  .muted {
    color: var(--ink-soft);
  }

  .err {
    color: var(--accent);
    font-size: 13px;
  }

  .list {
    list-style: none;
    margin: 0;
    padding: 0;
    border: 1px solid var(--rule);
    border-radius: var(--radius);
    overflow: hidden;
  }
</style>
