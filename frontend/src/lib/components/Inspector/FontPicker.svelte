<script lang="ts">
  import { config } from "../../stores/config";
  import { addFont, injectFont } from "../../render/fonts";

  interface Props {
    value: string;
    onChange: (family: string) => void;
  }
  let { value, onChange }: Props = $props();

  let adding = $state(false);
  let newFamily = $state("");
  let error = $state("");
  let busy = $state(false);

  // Make sure every listed font is injected so the dropdown previews render.
  $effect(() => {
    for (const f of $config.fonts) injectFont(f);
  });

  async function submitNew(): Promise<void> {
    const family = newFamily.trim();
    if (!family) return;
    busy = true;
    error = "";
    try {
      const fonts = await addFont(family);
      config.update((c) => ({ ...c, fonts }));
      onChange(family);
      newFamily = "";
      adding = false;
    } catch (e) {
      error = e instanceof Error ? e.message : "Could not add font";
    }
    busy = false;
  }
</script>

<div class="font-picker">
  <select
    class="select"
    value={value}
    onchange={(e) => onChange((e.currentTarget as HTMLSelectElement).value)}
    style={`font-family: "${value}", sans-serif`}
  >
    {#each $config.fonts as f}
      <option value={f} style={`font-family: "${f}", sans-serif`}>{f}</option>
    {/each}
  </select>
  <button class="btn btn-ghost btn-icon" title="Add a Google Font" onclick={() => (adding = !adding)}>
    +
  </button>
</div>

{#if adding}
  <div class="add-row">
    <input
      class="input"
      placeholder="Google Font name, e.g. Pacifico"
      bind:value={newFamily}
      onkeydown={(e) => e.key === "Enter" && submitNew()}
    />
    <button class="btn" disabled={busy} onclick={submitNew}>
      {busy ? "Adding…" : "Add"}
    </button>
  </div>
  {#if error}<div class="err">{error}</div>{/if}
{/if}

<style>
  .font-picker {
    display: flex;
    gap: 6px;
    align-items: center;
  }

  .add-row {
    display: flex;
    gap: 6px;
    margin-top: 6px;
  }

  .err {
    margin-top: 5px;
    font-size: 12px;
    color: var(--accent);
  }
</style>
