/**
 * Exportación: CSV (UTF-8 con BOM, separador «,», texto entre comillas) y JSON, entregados con la capacidad `downloads`
 * del visor (confirmación del visor). Sin la capacidad (vista previa, host sin permiso) se intenta el portapapeles.
 * Las cifras van tal como se muestran (convención es-EC), pensadas para leer o pegar, no para recalcular.
 */
import { errorCode, useDownloads } from "@/lib/capabilities";

export type SaveOutcome = { status: "saved" } | { status: "copied" } | { status: "declined" } | { status: "error"; code: string };

const csvCell = (v: unknown): string => {
  const s = v === null || v === undefined ? "" : String(v).replace(/ | /g, " ").trim();
  return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};

export function toCsv(rows: unknown[][]): string {
  return "﻿" + rows.map((r) => r.map(csvCell).join(",")).join("\r\n") + "\r\n";
}

/** Filas (cabecera + cuerpo) de una <table> tal como se ve: textContent de cada celda. */
export function tableToRows(table: HTMLTableElement): string[][] {
  const rows: string[][] = [];
  table.querySelectorAll("thead tr, tbody tr").forEach((tr) => {
    const cells = Array.from(tr.querySelectorAll("th, td"));
    if (cells.length === 0) return;
    // filas de sección (una sola celda con colspan) se conservan como una fila de un texto
    rows.push(cells.map((c) => (c.textContent ?? "").replace(/\s+/g, " ").trim()));
  });
  return rows;
}

export function stamp(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`;
}

export function safeName(s: string): string {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^A-Za-z0-9._-]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 80) || "export";
}

/** Guarda con `downloads`; si no está, copia al portapapeles. */
export async function saveText(filename: string, data: string): Promise<SaveOutcome> {
  const dl = await useDownloads();
  if (dl) {
    try {
      await dl.save({ filename, data });
      return { status: "saved" };
    } catch (e) {
      const code = errorCode(e);
      if (code === "declined") return { status: "declined" };
      if (code !== "unavailable" && code !== "not_granted" && code !== "capability_disabled") return { status: "error", code };
    }
  }
  try {
    await navigator.clipboard.writeText(data.replace(/^﻿/, ""));
    return { status: "copied" };
  } catch {
    return { status: "error", code: "unavailable" };
  }
}

export function outcomeText(o: SaveOutcome, what = "archivo"): string {
  switch (o.status) {
    case "saved": return `${what} guardado`;
    case "copied": return `sin permiso de descarga en esta vista: ${what} copiado al portapapeles`;
    case "declined": return "descarga cancelada";
    case "error": return `no se pudo exportar (${o.code})`;
  }
}
