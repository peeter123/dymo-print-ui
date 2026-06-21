import { writable } from "svelte/store";
import { api } from "../api";
import { config } from "./config";
import { get } from "svelte/store";

export type Reachability = "unknown" | "reachable" | "unreachable";

export const reachability = writable<Reachability>("unknown");

let timer: ReturnType<typeof setInterval> | null = null;

/** Check the configured printer's reachability once and update the store. */
export async function refreshStatus(): Promise<void> {
  const mac = get(config).printer_mac;
  if (!mac) {
    reachability.set("unknown");
    return;
  }
  try {
    const s = await api.printerStatus();
    reachability.set(s.reachable ? "reachable" : "unreachable");
  } catch {
    reachability.set("unreachable");
  }
}

/** Begin polling reachability on an interval (idempotent). */
export function startStatusPolling(intervalMs = 20000): void {
  if (timer) return;
  void refreshStatus();
  timer = setInterval(() => void refreshStatus(), intervalMs);
}

export function stopStatusPolling(): void {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
}
