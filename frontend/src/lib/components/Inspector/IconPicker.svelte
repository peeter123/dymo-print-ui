<script lang="ts">
  import { api } from "../../api";

  interface Props {
    onPick: (name: string) => void;
    onClose: () => void;
  }
  let { onPick, onClose }: Props = $props();

  const PAGE = 80;

  let query = $state("");
  let icons = $state<string[]>([]);
  let loading = $state(false);
  let exhausted = $state(false);
  let gridEl = $state<HTMLDivElement>();

  /** Reset and run a fresh search for the current query. */
  async function search(): Promise<void> {
    loading = true;
    exhausted = false;
    try {
      const first = await api.searchIcons(query, PAGE, 0);
      icons = first;
      exhausted = first.length < PAGE;
    } catch (e) {
      console.error(e);
      icons = [];
    }
    loading = false;
    // After replacing results the grid may still have room — top it up.
    queueMicrotask(maybeLoadMore);
  }

  /** Append the next page (used for infinite scroll). */
  async function loadMore(): Promise<void> {
    if (loading || exhausted) return;
    loading = true;
    try {
      const next = await api.searchIcons(query, PAGE, icons.length);
      if (next.length === 0) {
        exhausted = true;
      } else {
        icons = [...icons, ...next];
        if (next.length < PAGE) exhausted = true;
      }
    } catch (e) {
      console.error(e);
    }
    loading = false;
  }

  /** If the grid isn't scrollable yet (few results), keep loading. */
  function maybeLoadMore(): void {
    if (!gridEl || exhausted || loading) return;
    if (gridEl.scrollHeight <= gridEl.clientHeight + 40) void loadMore();
  }

  function onScroll(): void {
    if (!gridEl) return;
    const nearBottom =
      gridEl.scrollTop + gridEl.clientHeight >= gridEl.scrollHeight - 120;
    if (nearBottom) void loadMore();
  }

  let timer: ReturnType<typeof setTimeout>;
  function onInput(): void {
    clearTimeout(timer);
    timer = setTimeout(search, 180);
  }

  // Initial set.
  search();
</script>

<div
  class="overlay"
  role="presentation"
  onclick={(e) => e.target === e.currentTarget && onClose()}
>
  <div class="picker" role="dialog" aria-label="Choose an icon">
    <div class="picker-head">
      <span class="eyebrow">Material Design Icons</span>
      <input
        class="input search"
        placeholder="Search icons — home, lightbulb, wifi…"
        bind:value={query}
        oninput={onInput}
      />
    </div>

    {#if loading && icons.length === 0}
      <div class="empty">Searching…</div>
    {:else if icons.length === 0}
      <div class="empty">No icons match “{query}”.</div>
    {:else}
      <div class="grid" bind:this={gridEl} onscroll={onScroll}>
        {#each icons as name (name)}
          <button class="cell" title={name} onclick={() => onPick(name)}>
            <img src={`/api/icons/${name}.svg`} alt={name} class="ico" loading="lazy" />
            <span class="ico-name">{name}</span>
          </button>
        {/each}
        {#if loading}
          <div class="more">Loading…</div>
        {:else if exhausted}
          <div class="more">— end —</div>
        {/if}
      </div>
    {/if}
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

  .picker {
    width: min(680px, 92vw);
    height: 70vh;
    max-height: 78vh;
    display: flex;
    flex-direction: column;
    background: var(--paper-raised);
    border: 1px solid var(--rule-strong);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow);
    overflow: hidden;
  }

  .picker-head {
    padding: 16px 18px 12px;
    border-bottom: 1px solid var(--rule);
    display: flex;
    flex-direction: column;
    gap: 9px;
  }

  .search {
    font-size: 15px;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(92px, 1fr));
    gap: 4px;
    padding: 14px;
    overflow-y: auto;
    flex: 1;
    min-height: 0;
  }

  .more {
    grid-column: 1 / -1;
    text-align: center;
    padding: 14px;
    font-size: 12px;
    color: var(--ink-faint);
  }

  .cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 12px 6px 8px;
    border: 1px solid transparent;
    border-radius: var(--radius);
    background: transparent;
  }

  .cell:hover {
    border-color: var(--rule-strong);
    background: #fff;
  }

  .ico {
    width: 26px;
    height: 26px;
  }

  .ico-name {
    font-size: 10px;
    color: var(--ink-faint);
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .empty {
    padding: 40px;
    text-align: center;
    color: var(--ink-faint);
  }
</style>
