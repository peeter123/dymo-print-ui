import type { AppConfig, PrinterInfo, LabelDoc, HistoryEntrySummary, HistoryEntryDetail } from "./types";

async function jsonGet<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  async health(): Promise<{ status: string }> {
    return jsonGet("/api/health");
  },

  async getConfig(): Promise<AppConfig> {
    return jsonGet("/api/config");
  },

  async putConfig(patch: Partial<AppConfig>): Promise<AppConfig> {
    const res = await fetch("/api/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async scanPrinters(): Promise<PrinterInfo[]> {
    const data = await jsonGet<{ printers: PrinterInfo[] }>("/api/printers");
    return data.printers;
  },

  async printerStatus(): Promise<{ configured_mac: string | null; reachable: boolean }> {
    return jsonGet("/api/printer/status");
  },

  async savePrinter(mac: string, name: string | null): Promise<AppConfig> {
    const res = await fetch("/api/config/printer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mac, name }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getFonts(): Promise<string[]> {
    const data = await jsonGet<{ fonts: string[] }>("/api/fonts");
    return data.fonts;
  },

  async addFont(family: string): Promise<string[]> {
    const res = await fetch("/api/fonts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ family }),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(detail.detail ?? "Could not add font");
    }
    const data = (await res.json()) as { fonts: string[] };
    return data.fonts;
  },

  async removeFont(family: string): Promise<string[]> {
    const res = await fetch(`/api/fonts/${encodeURIComponent(family)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(await res.text());
    const data = (await res.json()) as { fonts: string[] };
    return data.fonts;
  },

  async searchIcons(q: string, limit = 80, offset = 0): Promise<string[]> {
    const data = await jsonGet<{ icons: { name: string }[] }>(
      `/api/icons?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`,
    );
    return data.icons.map((i) => i.name);
  },

  async iconPath(name: string): Promise<{ path: string; viewBox: string }> {
    return jsonGet(`/api/icons/${name}`);
  },

  /** POST a rendered PNG to print. Returns the printer outcome. */
  async print(
    png: Blob,
    doc: LabelDoc,
    opts: { copies: number; stretch: number; dither: boolean; padding: number },
  ): Promise<{
    result: string;
    code: number;
    low_battery: boolean;
    width: number;
    height: number;
  }> {
    const form = new FormData();
    form.append("image", png, "label.png");
    form.append("copies", String(opts.copies));
    form.append("stretch", String(opts.stretch));
    form.append("dither", String(opts.dither));
    form.append("padding", String(opts.padding));
    form.append("document", JSON.stringify(doc));
    const res = await fetch("/api/print", { method: "POST", body: form });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(detail.detail ?? "Print failed");
    }
    return res.json();
  },

  async getHistory(): Promise<HistoryEntrySummary[]> {
    const data = await jsonGet<{ entries: HistoryEntrySummary[] }>("/api/history");
    return data.entries;
  },

  async getHistoryEntry(id: string): Promise<HistoryEntryDetail> {
    return jsonGet(`/api/history/${id}`);
  },

  async deleteHistoryEntry(id: string): Promise<void> {
    const res = await fetch(`/api/history/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(await res.text());
  },

  async reprintHistoryEntry(
    id: string,
    copies: number,
  ): Promise<{ result: string; code: number; low_battery: boolean; width: number; height: number }> {
    const form = new FormData();
    form.append("copies", String(copies));
    const res = await fetch(`/api/history/${id}/reprint`, { method: "POST", body: form });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(detail.detail ?? "Reprint failed");
    }
    return res.json();
  },

  /** Save the current editor state to history without printing it. */
  async saveHistoryDraft(
    png: Blob,
    doc: LabelDoc,
    opts: { stretch: number; dither: boolean; padding: number },
  ): Promise<HistoryEntrySummary> {
    const form = new FormData();
    form.append("image", png, "label.png");
    form.append("document", JSON.stringify(doc));
    form.append("stretch", String(opts.stretch));
    form.append("dither", String(opts.dither));
    form.append("padding", String(opts.padding));
    const res = await fetch("/api/history", { method: "POST", body: form });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(detail.detail ?? "Could not save to history");
    }
    return res.json();
  },
};
