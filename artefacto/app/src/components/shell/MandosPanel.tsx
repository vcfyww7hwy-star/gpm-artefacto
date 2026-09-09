import { RotateCcw, X } from "lucide-react";
import { useState, type ReactNode } from "react";

import { ScenariosPanel } from "@/components/shell/ScenariosPanel";
import type { Scenario } from "@/model/scenarios";

import { Button } from "@/components/ui/button";
import type { Inputs } from "@/engine";
import { fmtNum, fmtPct, fmtX } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useModel } from "@/model/store";

interface Props {
  onClose: () => void;
  onCompare: (scenarios: Scenario[]) => void;
  className?: string;
}

function Group({ title, guide, children }: { title: string; guide?: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-2.5">
      <header>
        <h3 className="text-[11px] font-medium uppercase tracking-[0.06em] text-ink-3">{title}</h3>
        {guide && <p className="text-[11px] text-ink-3">{guide}</p>}
      </header>
      {children}
    </section>
  );
}

function Field({ label, name, value, dirty, children }: { label: string; name: string; value: string; dirty: boolean; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="flex items-baseline justify-between gap-2 text-[12px]">
        <span className={cn("text-ink-2", dirty && "text-accent")} title={name}>{label}</span>
        <span className={cn("font-medium text-ink", dirty && "text-accent")} style={{ fontVariantNumeric: "tabular-nums" }}>{value}</span>
      </span>
      {children}
    </label>
  );
}

function Range({ value, min, max, step, onChange }: { value: number; min: number; max: number; step: number; onChange: (v: number) => void }) {
  return (
    <input
      type="range"
      className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-hairline accent-accent [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-accent"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
    />
  );
}

function Segmented<T extends string>({ value, options, onChange }: { value: T; options: readonly T[]; onChange: (v: T) => void }) {
  return (
    <div role="radiogroup" className="inline-flex h-7 items-stretch rounded-1 border border-hairline bg-surface p-px">
      {options.map((o) => (
        <button
          key={o}
          type="button"
          role="radio"
          aria-checked={o === value}
          onClick={() => onChange(o)}
          className={cn("rounded-[3px] px-2.5 text-[12px] text-ink-2 hover:text-ink", o === value && "bg-accent-soft font-medium text-accent")}
        >
          {o}
        </button>
      ))}
    </div>
  );
}

/**
 * Cajón «Mandos»: el único lugar donde se edita. Maqueta: los ocho maestros, la fila Custom del bloque B y tres sensibilidades.
 * Cada cambio recalcula los 111 casos; «volver al libro» restaura la v3.1 entregada. Los cambios viven en la sesión (no se guardan).
 */
export function MandosPanel({ onClose, onCompare, className }: Props) {
  const m = useModel();
  const i = m.inputs;
  const [tab, setTab] = useState<"mandos" | "escenarios">("mandos");
  const dirty = (k: keyof Inputs) => m.dirtyKeys.includes(k);
  const setB = <K extends "Esc_Energia" | "Esc_Factor_CAPEX" | "Esc_Peaje" | "Esc_EscTarifa" | "Esc_Disponibilidad" | "Esc_Escalacion_CAPEX">(key: K, v: Inputs[K][number]) => {
    const arr = [...(i[key] as unknown[])];
    arr[0] = v;
    m.setInput(key, arr as Inputs[K]);
  };

  return (
    <aside id="mandos" aria-label="Mandos" className={cn("flex min-h-0 flex-col border-l border-hairline bg-surface", className)}>
      <header className="flex h-10 shrink-0 items-center justify-between border-b border-hairline pl-3 pr-2">
        <div role="tablist" className="flex items-center gap-1">
          {(["mandos", "escenarios"] as const).map((t) => (
            <button
              key={t}
              type="button"
              role="tab"
              aria-selected={tab === t}
              onClick={() => setTab(t)}
              className={cn("rounded-1 px-2 py-1 text-[13px] text-ink-2 hover:text-ink", tab === t && "bg-accent-soft font-medium text-accent")}
            >
              {t === "mandos" ? "Mandos" : "Escenarios"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="xs" onClick={m.reset} disabled={m.dirty === 0} title="Restaurar los valores del libro v3.1">
            <RotateCcw aria-hidden /> libro
          </Button>
          <Button variant="ghost" size="icon-xs" onClick={onClose} aria-label="Cerrar mandos">
            <X aria-hidden />
          </Button>
        </div>
      </header>
      {tab === "escenarios" && (
        <div className="flex min-h-0 flex-1 flex-col overflow-auto p-4">
          <ScenariosPanel onCompare={onCompare} />
        </div>
      )}
      <div className={cn("flex min-h-0 flex-1 flex-col gap-6 overflow-auto p-4", tab !== "mandos" && "hidden")}>
        <p className="text-[11.5px] text-ink-3">
          Tinta = editable. {m.dirty === 0 ? "Valores del libro v3.1 (08-sep-2026)." : `${m.dirty} entrada${m.dirty > 1 ? "s" : ""} distinta${m.dirty > 1 ? "s" : ""} del libro (sandbox de esta sesión).`}
        </p>

        <Group title="Maestros del diseño" guide="compartidos por los cuatro casos">
          <Field label="Potencia DC" name="Potencia_DC" value={`${fmtNum(i.Potencia_DC, 0)} kWp`} dirty={dirty("Potencia_DC")}>
            <Segmented value={String(i.Potencia_DC)} options={["5000", "6000", "7000", "8000"] as const} onChange={(v) => m.setInput("Potencia_DC", Number(v))} />
          </Field>
          <Field label="Ratio DC/AC" name="Ratio_DCAC" value={fmtX(i.Ratio_DCAC, 2)} dirty={dirty("Ratio_DCAC")}>
            <Range value={i.Ratio_DCAC} min={1.1} max={1.5} step={0.01} onChange={(v) => m.setInput("Ratio_DCAC", Math.round(v * 100) / 100)} />
          </Field>
          <Field label="Compra el terreno" name="Comprador_Terreno" value={i.Comprador_Terreno} dirty={dirty("Comprador_Terreno")}>
            <Segmented value={i.Comprador_Terreno} options={["SALELGI", "Exergy"] as const} onChange={(v) => m.setInput("Comprador_Terreno", v)} />
          </Field>
          <Field label="Tasa de descuento" name="Tasa_Descuento" value={fmtPct(i.Tasa_Descuento, 1)} dirty={dirty("Tasa_Descuento")}>
            <Range value={i.Tasa_Descuento} min={0.06} max={0.14} step={0.005} onChange={(v) => m.setInput("Tasa_Descuento", v)} />
          </Field>
          <Field label="Deuda / CAPEX" name="Pct_Apalancamiento" value={fmtPct(i.Pct_Apalancamiento, 0)} dirty={dirty("Pct_Apalancamiento")}>
            <Range value={i.Pct_Apalancamiento} min={0} max={1} step={0.05} onChange={(v) => m.setInput("Pct_Apalancamiento", v)} />
          </Field>
          <Field label="Tasa de la deuda" name="Tasa_Deuda" value={fmtPct(i.Tasa_Deuda, 2)} dirty={dirty("Tasa_Deuda")}>
            <Range value={i.Tasa_Deuda} min={0.05} max={0.12} step={0.0025} onChange={(v) => m.setInput("Tasa_Deuda", v)} />
          </Field>
          <Field label="Plazo de la deuda" name="Plazo_Deuda" value={`${i.Plazo_Deuda} años`} dirty={dirty("Plazo_Deuda")}>
            <Segmented value={String(i.Plazo_Deuda)} options={["6", "8", "10", "12", "15"] as const} onChange={(v) => m.setInput("Plazo_Deuda", Number(v))} />
          </Field>
          <Field label="Deducción adicional aplicable" name="Aplica_DedAd" value={i.Aplica_DedAd} dirty={dirty("Aplica_DedAd")}>
            <Segmented value={i.Aplica_DedAd} options={["Sí", "No"] as const} onChange={(v) => m.setInput("Aplica_DedAd", v)} />
          </Field>
        </Group>

        <Group title="Bloque B · caso Custom" guide="lo único que distingue a los cuatro casos; C · B · F no se tocan">
          <Field label="Energía" name="Escenario_Energia" value={i.Esc_Energia[0]} dirty={dirty("Esc_Energia")}>
            <Segmented value={i.Esc_Energia[0] as "P50" | "P90"} options={["P50", "P90"] as const} onChange={(v) => setB("Esc_Energia", v)} />
          </Field>
          <Field label="Factor CAPEX (× bottom-up)" name="Factor_CAPEX" value={fmtX(i.Esc_Factor_CAPEX[0], 2)} dirty={dirty("Esc_Factor_CAPEX")}>
            <Range value={i.Esc_Factor_CAPEX[0]} min={0.8} max={1.3} step={0.01} onChange={(v) => setB("Esc_Factor_CAPEX", Math.round(v * 100) / 100)} />
          </Field>
          <Field label="Peaje SGDA desde 2029" name="Peaje_SGDA" value={`${fmtNum(i.Esc_Peaje[0] * 100, 2)} ¢/kWh`} dirty={dirty("Esc_Peaje")}>
            <Range value={i.Esc_Peaje[0]} min={0} max={0.02} step={0.0025} onChange={(v) => setB("Esc_Peaje", v)} />
          </Field>
          <Field label="Escalación de la tarifa" name="Escalacion_Tarifa" value={`${fmtPct(i.Esc_EscTarifa[0], 1)}/año`} dirty={dirty("Esc_EscTarifa")}>
            <Range value={i.Esc_EscTarifa[0]} min={0} max={0.04} step={0.005} onChange={(v) => setB("Esc_EscTarifa", v)} />
          </Field>
          <Field label="Disponibilidad" name="Disponibilidad" value={fmtPct(i.Esc_Disponibilidad[0], 0)} dirty={dirty("Esc_Disponibilidad")}>
            <Range value={i.Esc_Disponibilidad[0]} min={0.9} max={1} step={0.005} onChange={(v) => setB("Esc_Disponibilidad", v)} />
          </Field>
          <Field label="Escalación del CAPEX hasta la compra" name="Escalacion_CAPEX" value={`${fmtPct(i.Esc_Escalacion_CAPEX[0], 0)}/año`} dirty={dirty("Esc_Escalacion_CAPEX")}>
            <Range value={i.Esc_Escalacion_CAPEX[0]} min={0} max={0.08} step={0.005} onChange={(v) => setB("Esc_Escalacion_CAPEX", v)} />
          </Field>
        </Group>

        <Group title="Pasos de la sensibilidad" guide="anchura de las barras del tornado y de las matrices">
          <Field label="CAPEX ±" name="Sens_CAPEX" value={fmtPct(i.Sens_CAPEX, 0)} dirty={dirty("Sens_CAPEX")}>
            <Range value={i.Sens_CAPEX} min={0.05} max={0.3} step={0.025} onChange={(v) => m.setInput("Sens_CAPEX", v)} />
          </Field>
          <Field label="Tarifa ±" name="Sens_Tarifa" value={fmtPct(i.Sens_Tarifa, 0)} dirty={dirty("Sens_Tarifa")}>
            <Range value={i.Sens_Tarifa} min={0.05} max={0.3} step={0.025} onChange={(v) => m.setInput("Sens_Tarifa", v)} />
          </Field>
          <Field label="Peaje del tornado" name="Sens_Peaje" value={`${fmtNum(i.Sens_Peaje * 100, 2)} ¢/kWh`} dirty={dirty("Sens_Peaje")}>
            <Range value={i.Sens_Peaje} min={0.0025} max={0.03} step={0.0025} onChange={(v) => m.setInput("Sens_Peaje", v)} />
          </Field>
        </Group>

        <p className="mt-auto border-t border-hairline pt-3 text-[11px] text-ink-3">
          Mandos rápidos: 21 de las 88 entradas de 01_Supuestos; el resto se edita en Supuestos. Los valores viven en la sesión; para conservarlos, guárdelos como escenario en la pestaña Escenarios.
        </p>
      </div>
    </aside>
  );
}
