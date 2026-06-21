import { writable } from "svelte/store";
import type { AppConfig } from "../types";
import { api } from "../api";

const DEFAULT: AppConfig = {
  printer_mac: null,
  printer_name: null,
  default_stretch: 2,
  default_dither: false,
  fonts: [],
};

export const config = writable<AppConfig>(DEFAULT);

export async function loadConfig(): Promise<AppConfig> {
  const c = await api.getConfig();
  config.set(c);
  return c;
}
