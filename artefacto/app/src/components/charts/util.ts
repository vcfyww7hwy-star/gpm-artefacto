import { useEffect, useRef, useState } from "react";

/** Escala lineal mínima (dominio → rango) con `nice` para ejes. */
export function linear(domain: [number, number], range: [number, number]) {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const k = d1 === d0 ? 0 : (r1 - r0) / (d1 - d0);
  const f = (x: number) => r0 + (x - d0) * k;
  f.invert = (y: number) => (k === 0 ? d0 : d0 + (y - r0) / k);
  f.domain = domain;
  f.range = range;
  return f;
}

/** Ticks «bonitos» (1-2-5) para un dominio; n ≈ número deseado. */
export function ticks(d0: number, d1: number, n = 5): number[] {
  if (d0 === d1) return [d0];
  const span = d1 - d0;
  const raw = span / n;
  const p = Math.pow(10, Math.floor(Math.log10(raw)));
  const m = raw / p;
  // umbrales geométricos (√2, √10, √50) como d3-array: evitan saltar a un paso tan ancho que deje un solo tick
  const step = (m >= 7.071 ? 10 : m >= 3.162 ? 5 : m >= 1.414 ? 2 : 1) * p;
  const start = Math.ceil(d0 / step) * step;
  const out: number[] = [];
  for (let v = start; v <= d1 + 1e-12; v += step) out.push(Math.round(v / step) * step + 0); // «+ 0» normaliza −0
  return out;
}

/** Ancho del contenedor (ResizeObserver) para SVG responsivos. */
export function useMeasure<T extends HTMLElement>(): [React.RefObject<T | null>, number] {
  const ref = useRef<T | null>(null);
  const [w, setW] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    setW(el.clientWidth);
    if (typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) setW(Math.floor(e.contentRect.width));
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, w];
}

/** Relleno divergente centrado en un umbral: mezcla del color de polo con la superficie según la distancia (0–maxPct). */
export function divergingFill(value: number, center: number, halfSpan: number, poleLow: string, poleHigh: string, maxPct = 72): string {
  if (!Number.isFinite(value) || halfSpan <= 0) return "var(--surface)";
  const d = (value - center) / halfSpan;
  const pct = Math.min(1, Math.abs(d)) * maxPct;
  const pole = d < 0 ? poleLow : poleHigh;
  return `color-mix(in oklab, ${pole} ${pct.toFixed(1)}%, var(--surface))`;
}
