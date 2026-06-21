<script lang="ts">
  import { onMount } from "svelte";
  import { config } from "../../stores/config";
  import { reachability, refreshStatus } from "../../stores/printerStatus";
  import { api } from "../../api";
  import type { PrinterInfo } from "../../types";
  import FontManager from "./FontManager.svelte";

  let scanning = $state(false);
  let found = $state<PrinterInfo[]>([]);
  let scanError = $state("");
  let manualMac = $state("");

  const macPattern = /^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}$/;

  onMount(refreshStatus);

  async function scan(): Promise<void> {
    scanning = true;
    scanError = "";
    found = [];
    try {
      found = await api.scanPrinters();
      if (found.length === 0) scanError = "No printers found. Make sure the LetraTag is awake (press a button) and try again.";
    } catch (e) {
      scanError = e instanceof Error ? e.message : "Scan failed";
    }
    scanning = false;
  }

  async function choose(p: PrinterInfo): Promise<void> {
    const cfg = await api.savePrinter(p.mac, p.name);
    config.set(cfg);
    await refreshStatus();
  }

  async function saveManual(): Promise<void> {
    if (!macPattern.test(manualMac.trim())) {
      scanError = "That doesn't look like a MAC address (AA:BB:CC:DD:EE:FF).";
      return;
    }
    const cfg = await api.savePrinter(manualMac.trim().toUpperCase(), null);
    config.set(cfg);
    manualMac = "";
    await refreshStatus();
  }

  async function forget(): Promise<void> {
    const cfg = await api.savePrinter("", null);
    config.set({ ...cfg, printer_mac: null, printer_name: null });
    await api.putConfig({ printer_mac: null, printer_name: null } as any);
    await refreshStatus();
  }
</script>

<div class="page">
  <section class="block">
    <header class="block-head">
      <span class="eyebrow">Printer</span>
      <h2>Your LetraTag</h2>
    </header>

    {#if $config.printer_mac}
      <div class="current">
        <div class="cur-info">
          <span class="badge" class:ok={$reachability === "reachable"} class:off={$reachability === "unreachable"}></span>
          <div>
            <div class="cur-name">{$config.printer_name ?? "LetraTag"}</div>
            <div class="cur-mac">{$config.printer_mac}</div>
          </div>
        </div>
        <div class="cur-actions">
          <span class="status-text">
            {#if $reachability === "unknown"}Checking…{:else if $reachability === "reachable"}In range{:else}Not in range{/if}
          </span>
          <button class="btn btn-ghost" onclick={refreshStatus}>Re-check</button>
          <button class="btn btn-ghost" onclick={forget}>Forget</button>
        </div>
      </div>
    {:else}
      <p class="muted">No printer configured yet. Scan to find one nearby, or enter its MAC address.</p>
    {/if}

    <div class="scan-row">
      <button class="btn" onclick={scan} disabled={scanning}>
        {scanning ? "Scanning…" : "Scan for printers"}
      </button>
    </div>

    {#if found.length}
      <ul class="found">
        {#each found as p}
          <li>
            <div>
              <div class="cur-name">{p.name}</div>
              <div class="cur-mac">{p.mac}</div>
            </div>
            <button class="btn btn-primary" onclick={() => choose(p)}>Use this</button>
          </li>
        {/each}
      </ul>
    {/if}

    {#if scanError}<p class="err">{scanError}</p>{/if}

    <details class="manual">
      <summary>Enter a MAC address manually</summary>
      <div class="manual-row">
        <input class="input" placeholder="AA:BB:CC:DD:EE:FF" bind:value={manualMac} />
        <button class="btn" onclick={saveManual}>Save</button>
      </div>
      <p class="hint">Useful when the printer is asleep during a scan but you know its address.</p>
    </details>
  </section>

  <section class="block">
    <FontManager />
  </section>
</div>

<style>
  .page {
    max-width: 720px;
    margin: 0 auto;
    padding: 40px 24px 80px;
    display: flex;
    flex-direction: column;
    gap: 34px;
  }

  .block-head {
    margin-bottom: 18px;
  }

  .block-head h2 {
    margin-top: 4px;
    font-size: 22px;
  }

  .current {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 16px 18px;
    background: var(--paper-raised);
    border: 1px solid var(--rule);
    border-radius: var(--radius);
    margin-bottom: 16px;
  }

  .cur-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .badge {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--ink-faint);
    flex-shrink: 0;
  }

  .badge.ok {
    background: #4f9d69;
    box-shadow: 0 0 0 3px rgba(79, 157, 105, 0.18);
  }

  .badge.off {
    background: var(--accent-soft);
  }

  .cur-name {
    font-weight: 600;
  }

  .cur-mac {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--ink-faint);
  }

  .cur-actions {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .status-text {
    font-size: 13px;
    color: var(--ink-soft);
    margin-right: 4px;
  }

  .scan-row {
    margin: 8px 0 14px;
  }

  .found {
    list-style: none;
    margin: 0 0 14px;
    padding: 0;
    border: 1px solid var(--rule);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .found li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: var(--paper-raised);
  }

  .found li + li {
    border-top: 1px solid var(--rule);
  }

  .muted {
    color: var(--ink-soft);
  }

  .err {
    color: var(--accent);
    font-size: 13px;
  }

  .manual {
    margin-top: 10px;
  }

  .manual summary {
    cursor: pointer;
    color: var(--ink-soft);
    font-size: 14px;
  }

  .manual-row {
    display: flex;
    gap: 8px;
    margin-top: 12px;
  }

  .hint {
    font-size: 12px;
    color: var(--ink-faint);
    margin: 8px 0 0;
  }
</style>
