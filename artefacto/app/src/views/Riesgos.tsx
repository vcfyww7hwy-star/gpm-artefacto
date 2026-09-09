import { useMemo, useState } from "react";

import { RiskMatrix, type RiskPoint } from "@/components/charts/RiskMatrix";
import { DataTable, type Column } from "@/components/DataTable";
import { Live, Trace } from "@/components/Live";
import { Status, stripGlyph } from "@/components/Status";
import { Chip, Note, Section, ViewHeader } from "@/components/ViewHeader";
import { fmtNum } from "@/lib/format";
import type { CaseId, ViewId } from "@/lib/views";
import { cn } from "@/lib/utils";
import { statusOf, type Book } from "@/model/book";
import type { Value } from "@/model/formula";
import { useModel } from "@/model/store";

/**
 * Matriz de riesgos (hoja 11_Riesgos): los 15 riesgos en la matriz probabilidad × impacto (3 × 3) y en una tabla ordenada por
 * score, con el nivel calculado como en la hoja (score ≥ Umbral_Riesgo_Alto → ■ ALTO; ≥ Umbral_Riesgo_Medio → ▲ MEDIO; si no
 * ● BAJO). Los umbrales son los de 01 §I (editables en Supuestos); los textos de riesgo y mitigación son los del libro,
 * evaluados con los valores actuales.
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

type Riesgo = Book["riesgos"]["rows"][number];

interface Item {
  /** número de fila en la hoja (1…15): identificador en la matriz y en la tabla */
  id: string;
  k: number;
  r: Riesgo;
  score: number;
  /** texto de la columna G de la hoja: «■ ALTO» · «▲ MEDIO» · «● BAJO» */
  nivel: string;
}

/** Número de una entrada de 01 que el Motor no usa (`m.extras`), o el respaldo. */
function numOf(v: Value | undefined, fallback: number): number {
  return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

/** Escala 1–3 de la matriz (la hoja sólo admite esos valores; cualquier otro se acota). */
function as123(v: number): 1 | 2 | 3 {
  return v <= 1 ? 1 : v >= 3 ? 3 : 2;
}

/** Nivel con la misma regla y los mismos textos que 11!G6:G20: =IF(score>=Umbral_Riesgo_Alto,"■ ALTO",IF(score>=Umbral_Riesgo_Medio,"▲ MEDIO","● BAJO")). */
function nivelDe(score: number, alto: number, medio: number): string {
  return score >= alto ? "■ ALTO" : score >= medio ? "▲ MEDIO" : "● BAJO";
}

export function Riesgos({ onNavigate }: Props) {
  const m = useModel();
  const R = m.book.riesgos;
  const [sel, setSel] = useState<string | null>(null);

  const alto = numOf(m.extras.Umbral_Riesgo_Alto, R.umbrales.alto);
  const medio = numOf(m.extras.Umbral_Riesgo_Medio, R.umbrales.medio);

  const items = useMemo<Item[]>(
    () =>
      R.rows.map((r, k) => {
        const score = r.prob * r.impacto;
        return { id: String(k + 1), k, r, score, nivel: nivelDe(score, alto, medio) };
      }),
    [R, alto, medio],
  );
  const sorted = useMemo(() => [...items].sort((a, b) => b.score - a.score || a.k - b.k), [items]);
  const points: RiskPoint[] = items.map((it) => ({ id: it.id, label: `${it.id} · ${it.r.categoria} · ${m.live(it.r.riesgo)}`, prob: as123(it.r.prob), impacto: as123(it.r.impacto) }));
  const nAlto = items.filter((it) => statusOf(it.nivel) === "risk").length;
  const nMedio = items.filter((it) => statusOf(it.nivel) === "warn").length;
  const nBajo = items.length - nAlto - nMedio;
  const selItem = sel === null ? null : items.find((it) => it.id === sel) ?? null;

  // cabeceras de la hoja (B5:I5) + «Alerta temprana» (J5, columna del disparador)
  const H = (R.headers ?? []).map((h) => h.replace(/\s*\n\s*/g, " "));
  const hd = (k: number, fallback: string) => H[k] ?? fallback;

  const columns: Column<Item>[] = [
    { key: "id", label: "#", mono: true, nowrap: true, width: "36px", render: (it) => <span className="text-ink-3">{it.id}</span> },
    { key: "cat", label: hd(0, "Categoría"), width: "10%", nowrap: false, render: (it) => <span className="font-medium text-ink">{it.r.categoria}</span> },
    { key: "riesgo", label: hd(1, "Riesgo"), width: "26%", render: (it) => <Live text={it.r.riesgo} className="text-ink" /> },
    { key: "prob", label: hd(2, "Prob. (1-3)"), align: "right", nowrap: true, render: (it) => fmtNum(it.r.prob, 0) },
    { key: "imp", label: hd(3, "Impacto (1-3)"), align: "right", nowrap: true, render: (it) => fmtNum(it.r.impacto, 0) },
    { key: "score", label: hd(4, "Score"), align: "right", nowrap: true, render: (it) => <span className="font-medium text-ink">{fmtNum(it.score, 0)}</span> },
    { key: "nivel", label: hd(5, "Nivel"), nowrap: true, render: (it) => <Status kind={statusOf(it.nivel)} className="text-[11.5px]">{stripGlyph(it.nivel)}</Status> },
    { key: "mit", label: hd(6, "Mitigación"), width: "26%", render: (it) => <Live text={it.r.mitigacion} className="text-ink-2" /> },
    { key: "dueno", label: hd(7, "Dueño"), width: "9%", render: (it) => <span className="text-ink-2">{it.r.dueno}</span> },
    { key: "disp", label: "Alerta temprana", width: "12%", render: (it) => <span className="text-ink-3">{it.r.disparador}</span> },
  ];

  const dirty = (name: string) => m.dirtyExtras.includes(name);

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="Matriz de riesgos" sheet="11_Riesgos">
        <Chip title="01_Supuestos §I · Umbral_Riesgo_Alto" className={cn(dirty("Umbral_Riesgo_Alto") && "border-accent text-accent")}>
          Umbral_Riesgo_Alto · score ≥ {fmtNum(alto, 0)}
        </Chip>
        <Chip title="01_Supuestos §I · Umbral_Riesgo_Medio" className={cn(dirty("Umbral_Riesgo_Medio") && "border-accent text-accent")}>
          Umbral_Riesgo_Medio · score ≥ {fmtNum(medio, 0)}
        </Chip>
        <Status kind="risk">{fmtNum(nAlto, 0)} {nAlto === 1 ? "alto" : "altos"}</Status>
        <Status kind="warn">{fmtNum(nMedio, 0)} {nMedio === 1 ? "medio" : "medios"}</Status>
        <Status kind="ok">{fmtNum(nBajo, 0)} {nBajo === 1 ? "bajo" : "bajos"}</Status>
      </ViewHeader>

      {/* matriz + detalle del riesgo seleccionado */}
      <Section title="Probabilidad × impacto" guide="fila = probabilidad, columna = impacto; el color de la celda es el nivel de su score frente a los umbrales · clic en un número para ver el riesgo">
        <div className="grid gap-6 lg:grid-cols-[auto_minmax(0,1fr)]">
          <RiskMatrix points={points} umbralAlto={alto} umbralMedio={medio} selected={sel} onSelect={setSel} />
          <aside className="flex flex-col gap-3 border-l border-hairline pl-5 text-[12.5px]">
            {selItem ? (
              <>
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span className="font-mono text-[10.5px] text-ink-3">#{selItem.id}</span>
                  <span className="text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">{selItem.r.categoria}</span>
                  <Status kind={statusOf(selItem.nivel)}>
                    {stripGlyph(selItem.nivel)} · p {fmtNum(selItem.r.prob, 0)} × i {fmtNum(selItem.r.impacto, 0)} = {fmtNum(selItem.score, 0)}
                  </Status>
                </div>
                <p className="text-[14px] font-semibold leading-snug text-ink">
                  <Live text={selItem.r.riesgo} />
                </p>
                <dl className="grid gap-x-6 gap-y-2 md:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
                  <div>
                    <dt className="text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">{hd(6, "Mitigación")}</dt>
                    <dd className="font-serif text-[13px] leading-[1.45] text-ink-2">
                      <Live text={selItem.r.mitigacion} />
                    </dd>
                  </div>
                  <div className="flex flex-col gap-2">
                    <div>
                      <dt className="text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">{hd(7, "Dueño")}</dt>
                      <dd className="text-ink">{selItem.r.dueno}</dd>
                    </div>
                    <div>
                      <dt className="text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">Alerta temprana</dt>
                      <dd className="text-ink">{selItem.r.disparador}</dd>
                    </div>
                  </div>
                </dl>
                <Trace cell={`11_Riesgos!C${6 + selItem.k}`} />
              </>
            ) : (
              <p className="text-ink-3">Seleccione un riesgo en la matriz o en la tabla para ver su mitigación, dueño y alerta temprana.</p>
            )}
          </aside>
        </div>
      </Section>

      {/* tabla ordenada por score */}
      <Section title={`Los ${fmtNum(items.length, 0)} riesgos ordenados por score`} guide="score = probabilidad × impacto; a igual score, el orden de la hoja · clic en una fila para verla en la matriz">
        <DataTable<Item>
          columns={columns}
          rows={sorted}
          rowKey={(it) => it.id}
          size="sm"
          selected={(it) => it.id === sel}
          onRowClick={(it) => setSel(sel === it.id ? null : it.id)}
          footer="Hoja 11_Riesgos, filas 6–20, columnas B–J; el número # es la fila de la hoja (1 = fila 6). Textos tal cual, evaluados con los valores actuales."
        />
      </Section>

      <Note>
        Los umbrales Umbral_Riesgo_Alto y Umbral_Riesgo_Medio se editan en{" "}
        <button type="button" className="text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid" onClick={() => onNavigate("supuestos")}>
          Supuestos
        </button>{" "}
        (01 §I). Los riesgos de mercado, fiscal y financiero se cuantifican en{" "}
        <button type="button" className="text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid" onClick={() => onNavigate("sensibilidad")}>
          Sensibilidad
        </button>
        ; el marco que los sustenta está en{" "}
        <button type="button" className="text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid" onClick={() => onNavigate("legal")}>
          Legal
        </button>
        .
      </Note>
    </div>
  );
}
