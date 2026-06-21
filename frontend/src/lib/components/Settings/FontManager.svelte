<script lang="ts">
  import { config } from "../../stores/config";
  import { addFont, injectFont } from "../../render/fonts";
  import { api } from "../../api";

  let newFamily = $state("");
  let busy = $state(false);
  let error = $state("");

  $effect(() => {
    for (const f of $config.fonts) injectFont(f);
  });

  async function add(): Promise<void> {
    const family = newFamily.trim();
    if (!family) return;
    busy = true;
    error = "";
    try {
      const fonts = await addFont(family);
      config.update((c) => ({ ...c, fonts }));
      newFamily = "";
    } catch (e) {
      error = e instanceof Error ? e.message : "Could not add font";
    }
    busy = false;
  }

  async function remove(family: string): Promise<void> {
    const fonts = await api.removeFont(family);
    config.update((c) => ({ ...c, fonts }));
  }
</script>

<header class="block-head">
  <span class="eyebrow">Typography</span>
  <h2>Fonts</h2>
</header>

<p class="muted">
  Any font on <a href="https://fonts.google.com" target="_blank" rel="noreferrer">Google Fonts</a>
  can be added by name. It's cached locally on first use, so it keeps working offline.
</p>

<div class="add-row">
  <input
    class="input"
    placeholder="Add a Google Font — e.g. Pacifico, Fira Sans…"
    bind:value={newFamily}
    onkeydown={(e) => e.key === "Enter" && add()}
  />
  <button class="btn" disabled={busy} onclick={add}>{busy ? "Adding…" : "Add"}</button>
</div>
{#if error}<p class="err">{error}</p>{/if}

<ul class="fonts">
  {#each $config.fonts as f}
    <li>
      <span class="sample" style={`font-family: "${f}", sans-serif`}>{f}</span>
      <button class="btn btn-ghost btn-icon" title="Remove" onclick={() => remove(f)}>✕</button>
    </li>
  {/each}
</ul>

<style>
  .block-head {
    margin-bottom: 14px;
  }

  .block-head h2 {
    margin-top: 4px;
    font-size: 22px;
  }

  .muted {
    color: var(--ink-soft);
    font-size: 14px;
  }

  .muted a {
    color: var(--accent);
  }

  .add-row {
    display: flex;
    gap: 8px;
    margin: 16px 0 6px;
  }

  .err {
    color: var(--accent);
    font-size: 13px;
  }

  .fonts {
    list-style: none;
    margin: 14px 0 0;
    padding: 0;
    border: 1px solid var(--rule);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .fonts li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: var(--paper-raised);
  }

  .fonts li + li {
    border-top: 1px solid var(--rule);
  }

  .sample {
    font-size: 18px;
  }
</style>
