<script lang="ts">
  import { onMount } from "svelte";
  import { loadConfig, config } from "./lib/stores/config";
  import { reachability, startStatusPolling } from "./lib/stores/printerStatus";
  import { injectFonts, injectUiFont } from "./lib/render/fonts";
  import Editor from "./lib/components/Editor/Editor.svelte";
  import PrinterPage from "./lib/components/Settings/PrinterPage.svelte";

  type View = "editor" | "settings";
  let view = $state<View>("editor");
  let ready = $state(false);

  onMount(async () => {
    injectUiFont();
    try {
      const cfg = await loadConfig();
      injectFonts(cfg.fonts);
      startStatusPolling();
    } catch (e) {
      console.error("Failed to load config", e);
    }
    ready = true;
  });

  const dotTitle = $derived(
    $reachability === "reachable"
      ? "Printer in range"
      : $reachability === "unreachable"
        ? "Printer configured but not in range"
        : "Printer configured",
  );
</script>

<div class="app">
  <header class="topbar">
    <div class="brand">
      <span class="brand-mark">▌▌▌</span>
      <span class="brand-name">Label Studio</span>
      <span class="brand-sub">Dymo LetraTag</span>
    </div>
    <nav class="nav">
      <button
        class="nav-link"
        class:active={view === "editor"}
        onclick={() => (view = "editor")}>Editor</button
      >
      <button
        class="nav-link"
        class:active={view === "settings"}
        onclick={() => (view = "settings")}
      >
        Printer
        {#if $config.printer_mac}
          <span
            class="dot"
            class:reachable={$reachability === "reachable"}
            class:unreachable={$reachability === "unreachable"}
            title={dotTitle}
          ></span>
        {/if}
      </button>
    </nav>
  </header>

  <main class="main">
    {#if !ready}
      <div class="loading">Loading…</div>
    {:else if view === "editor"}
      <Editor onGoToSettings={() => (view = "settings")} />
    {:else}
      <PrinterPage />
    {/if}
  </main>
</div>

<style>
  .app {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 22px;
    height: 56px;
    border-bottom: 1px solid var(--rule);
    background: var(--paper-raised);
  }

  .brand {
    display: flex;
    align-items: baseline;
    gap: 10px;
  }

  .brand-mark {
    color: var(--accent);
    letter-spacing: -2px;
    font-size: 18px;
  }

  .brand-name {
    font-weight: 600;
    letter-spacing: -0.02em;
    font-size: 17px;
  }

  .brand-sub {
    font-size: 12px;
    color: var(--ink-faint);
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  .nav {
    display: flex;
    gap: 4px;
  }

  .nav-link {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 7px 14px;
    border: none;
    background: transparent;
    border-radius: var(--radius);
    color: var(--ink-soft);
    font-weight: 500;
  }

  .nav-link:hover {
    background: rgba(28, 26, 23, 0.05);
  }

  .nav-link.active {
    color: var(--ink);
    background: rgba(28, 26, 23, 0.07);
  }

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--ink-faint);
  }

  .dot.reachable {
    background: #4f9d69;
    box-shadow: 0 0 0 2px rgba(79, 157, 105, 0.2);
  }

  .dot.unreachable {
    background: #d8902f;
    box-shadow: 0 0 0 2px rgba(216, 144, 47, 0.2);
  }

  .main {
    flex: 1;
    min-height: 0;
    overflow: auto;
  }

  .loading {
    display: grid;
    place-items: center;
    height: 100%;
    color: var(--ink-faint);
  }
</style>
