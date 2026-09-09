import { useMemo, useState } from "react";

import { Gantt, type GanttMarker, type GanttRow } from "@/components/charts/Gantt";
import { DataTable, type Column } from "@/components/DataTable";
import { Frozen, Live, Trace } from "@/components/Live";
import { Status, stripGlyph, type StatusKind } from "@/components/Status";
import { Chip, Note, Section, ViewHeader } from "@/components/ViewHeader";
import { dayNumber, daysInMonth, edate, formatISODate, parseISODate, type YMD } from "@/engine";
import { fmtDate, fmtMonthYear, fmtNum, fmtPct, fmtUSD } from "@/lib/format";
import type { CaseId, ViewId } from "@/lib/views";
import { cn } from "@/lib/utils";
import { statusOf, type Book } from "@/model/book";
import { capexTable } from "@/model/capex";
import type { Value } from "@/model/formula";
import { useModel } from "@/model/store";

/**
 * Trámites (hoja 03_Tramites): cronograma de los 17 hitos RC-xx en un Gantt mensual desde Mes1_Cronograma, con el COD implícito
 * (Meses_Construccion), la Fecha_COD objetivo y la ventana de vigencia de la Factibilidad de Conexión; tabla de hitos con todas las
 * columnas de la hoja; totales de costos de desarrollo frente al rubro 9 del CAPEX del caso seleccionado; memo estático de
 * escenarios. Los hitos (inicio, duración, costo) son los del libro: el artefacto no los edita.
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

type Hito = Book["tramites"]["rows"][number];

/** Vigencia de la Factibilidad de Conexión en meses (005/24 art. 13; misma constante que el control F12 de 13_Controles). */
const VIGENCIA_FACTIBILIDAD = 6;

/** Número de una entrada de 01 que el Motor no usa (`m.extras`), o el respaldo. */
function numOf(v: Value | undefined, fallback: number): number {
  return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

/** Fecha ISO → YMD sin lanzar (una fecha mal formada en Mandos no debe romper la vista). */
function safeDate(s: string): YMD | null {
  try {
    return parseISODate(s);
  } catch {
    return null;
  }
}

/** Meses (con fracción por día) entre dos fechas: posición de una fecha en el eje del Gantt (0 = inicio del mes 1). */
function monthsFrom(a: YMD, b: YMD): number {
  return (b.y - a.y) * 12 + (b.m - a.m) + (b.d - a.d) / daysInMonth(b.y, b.m);
}

/** Glifo del riesgo del hito (columna L de la hoja): Alto ■ · Medio-Alto y Medio ▲ · Bajo ● · otro ◇. */
function riesgoKind(r: string): StatusKind {
  const t = r.trim().toLowerCase();
  if (t === "alto") return "risk";
  if (t.startsWith("medio")) return "warn";
  if (t === "bajo") return "ok";
  return "info";
}

export function Tramites({ caseId, onNavigate }: Props) {
  const m = useModel();
  const T = m.book.tramites;
  const rows = T.rows;
  const [sel, setSel] = useState<string | null>(null);

  // --- eje temporal ------------------------------------------------------------------------------------------------------
  const mes1 = safeDate(T.mes1);
  const monthLabel = (k: number) => (mes1 ? fmtMonthYear(formatISODate(edate(mes1, k - 1))) : `mes ${k}`);
  const maxFin = rows.reduce((s, r) => Math.max(s, r.fin), 0);

  // COD implícito (Meses_Construccion = Mes_COD_Cron del libro) frente a la Fecha_COD objetivo del modelo (control 03!M5)
  const mesCOD = m.inputs.Meses_Construccion;
  const codDate = mes1 && Number.isFinite(mesCOD) ? edate(mes1, Math.trunc(mesCOD)) : null; // EDATE trunca los meses, como Excel
  const fechaCOD = safeDate(m.inputs.Fecha_COD);
  const tolDias = numOf(m.extras.Tol_Dias_COD, numOf(m.book.calc_names.Tol_Dias_COD, 0));
  const diffDias = codDate && fechaCOD ? Math.abs(dayNumber(codDate) - dayNumber(fechaCOD)) : null;
  const cronText = diffDias === null ? "▲ revisar Fecha_COD" : diffDias <= tolDias ? "● coherente con Fecha_COD del modelo" : "▲ revisar Fecha_COD";
  const fechaPos = mes1 && fechaCOD ? monthsFrom(mes1, fechaCOD) : null;

  // ventana de vigencia de la Factibilidad (RC-09) y control F12 (RC-10 debe terminar dentro)
  const rc09 = rows.find((r) => r.id === "RC-09") ?? null;
  const rc10 = rows.find((r) => r.id === "RC-10") ?? null;
  const gapF12 = rc09 && rc10 ? rc10.fin - rc09.fin : null;
  const f12Text =
    gapF12 === null ? null : gapF12 <= VIGENCIA_FACTIBILIDAD ? `● ok (${gapF12} meses)` : `■ ${gapF12} meses > ${VIGENCIA_FACTIBILIDAD}: la factibilidad vence antes de la habilitación — reordenar 03`;

  // eje: max(fin) + 1 meses (como la hoja), ampliado si el COD implícito o la Fecha_COD caen más allá
  const months = Math.max(1, maxFin + 1, codDate ? Math.ceil(mesCOD) + 1 : 1, fechaPos !== null && fechaPos > 0 ? Math.ceil(fechaPos) + 1 : 1);
  const sameCod = fechaPos !== null && Math.abs(fechaPos - mesCOD) < 0.5;
  const cronKind = statusOf(cronText);
  const markers: GanttMarker[] = [];
  if (codDate) {
    markers.push({
      month: mesCOD,
      label: sameCod ? `COD · ${fmtMonthYear(formatISODate(codDate))} = Fecha_COD` : `COD implícito · ${fmtMonthYear(formatISODate(codDate))}`,
      kind: sameCod && cronKind !== "ok" ? "warn" : "cod",
    });
  }
  if (!sameCod && fechaPos !== null && fechaPos >= 0 && fechaPos <= months) {
    markers.push({ month: fechaPos, label: `Fecha_COD · ${fmtDate(m.inputs.Fecha_COD)}`, kind: cronKind === "ok" ? "info" : "warn" });
  }
  // la etiqueta de la ventana se explica en la leyenda (el componente la dibuja sobre la fila de meses y taparía sus rótulos)
  const win = rc09 ? { from: rc09.fin + 1, to: rc09.fin + VIGENCIA_FACTIBILIDAD, label: "" } : undefined;
  const f12Ctl = m.book.controles.rows.find((r) => r.id === "F12") ?? null;

  const gantt: GanttRow[] = useMemo(
    () =>
      rows.map((r) => ({
        id: r.id,
        label: m.live(r.tramite),
        start: r.inicio,
        end: r.fin,
        critical: r.critica === "Sí",
        detail: `${r.autoridad} · ${fmtUSD(r.costo)} · riesgo ${r.riesgo}${r.critica === "Parcial" ? " · ruta crítica parcial (dibujada como no crítica)" : ""}`,
      })),
    [rows],
  );

  // --- totales frente al rubro 9 del CAPEX del caso (03!I25:I27) ------------------------------------------------------------
  const c = m.cases[m.idx(caseId)];
  const capex = capexTable(m.inputs, m.derived, c.params);
  const rubro9 = capex.rubros[8]?.costo ?? 0;
  const sumCostos = rows.reduce((s, r) => s + r.costo, 0);
  const tol = numOf(m.extras.Tol_Costo_Tramites, numOf(m.book.calc_names.Tol_Costo_Tramites, 0));
  const cabeText = sumCostos <= rubro9 * (1 + tol) ? "● cabe" : "▲ excede el rubro 9 — revisar";
  const margen = rubro9 * (1 + tol) - sumCostos;
  const lbl = (row: string, fallback: string) => T.totales[row]?.label ?? fallback;
  const nCrit = rows.filter((r) => r.critica === "Sí").length, nParcial = rows.filter((r) => r.critica === "Parcial").length;

  // --- tabla de hitos: todas las columnas de la hoja -------------------------------------------------------------------------
  const H = T.headers.map((h) => h.replace(/\s*\n\s*/g, " "));
  const hd = (k: number, fallback: string) => H[k] ?? fallback;
  const columns: Column<Hito>[] = [
    { key: "id", label: hd(0, "ID"), mono: true, nowrap: true, width: "56px", render: (r) => r.id },
    { key: "tramite", label: hd(1, "Trámite"), width: "24%", render: (r) => <span className="text-ink">{r.tramite}</span> },
    { key: "autoridad", label: hd(2, "Autoridad"), width: "11%", render: (r) => <span className="text-ink-2">{r.autoridad}</span> },
    { key: "base", label: hd(3, "Base legal"), width: "11%", render: (r) => <span className="text-ink-3">{r.base_legal}</span> },
    { key: "inicio", label: hd(4, "Inicio (mes)"), align: "right", nowrap: true, render: (r) => <span title={monthLabel(r.inicio)}>{fmtNum(r.inicio, 0)}</span> },
    { key: "dur", label: hd(5, "Dur. (m)"), align: "right", nowrap: true, render: (r) => fmtNum(r.dur, 0) },
    { key: "fin", label: hd(6, "Fin (mes)"), align: "right", nowrap: true, render: (r) => <span title={monthLabel(r.fin)}>{fmtNum(r.fin, 0)}</span> },
    { key: "costo", label: hd(7, "Costo [USD]"), align: "right", nowrap: true, render: (r) => fmtUSD(r.costo) },
    { key: "pred", label: hd(8, "Predecesor"), mono: true, nowrap: true, render: (r) => <span className="text-ink-3">{r.predecesor}</span> },
    {
      key: "critica",
      label: hd(9, "Ruta crítica"),
      nowrap: true,
      render: (r) =>
        r.critica === "Sí" ? (
          <span className="font-medium text-accent">{r.critica}</span>
        ) : r.critica === "Parcial" ? (
          <span className="text-ink-2" title="En el Gantt se dibuja como no crítica">{r.critica}</span>
        ) : (
          <span className="text-ink-3">{r.critica}</span>
        ),
    },
    { key: "riesgo", label: hd(10, "Riesgo"), nowrap: true, render: (r) => <Status kind={riesgoKind(r.riesgo)} className="text-[11.5px]">{r.riesgo}</Status> },
    { key: "nota", label: hd(11, "Nota"), width: "20%", render: (r) => <Live text={r.nota} className="text-ink-2" /> },
  ];

  const version = m.book.meta.version, corte = fmtDate(m.book.meta.fecha_analisis);
  const memoTitle = T.memo[0] ?? "Escenarios de cronograma — memo estático";

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="Trámites" sheet="03_Tramites">
        <Chip title="03_Tramites!D5 · Mes1_Cronograma">
          {m.book.sheets["03_Tramites"]?.labels["5"] ?? "Mes 1 del cronograma"} · {mes1 ? fmtMonthYear(T.mes1) : T.mes1}
        </Chip>
        <Chip title="03_Tramites!F5 · Mes_COD_Cron = MAX(fin)">Mes de COD (fin de RC-13) · {fmtNum(maxFin, 0)}</Chip>
        <Chip title="03_Tramites!K5 = EDATE(Mes1_Cronograma, Meses_Construccion)" className={cn(m.dirtyKeys.includes("Meses_Construccion") && "border-accent text-accent")}>
          Fecha de COD implícita · {codDate ? fmtDate(formatISODate(codDate)) : "—"}
        </Chip>
        <Chip title="01_Supuestos · Fecha_COD" className={cn(m.dirtyKeys.includes("Fecha_COD") && "border-accent text-accent")}>Fecha_COD · {fmtDate(m.inputs.Fecha_COD)}</Chip>
        <Status kind={cronKind}>
          {stripGlyph(cronText)} <Trace name="Check_Cron" cell="03_Tramites!M5" />
        </Status>
        {mesCOD !== maxFin && (
          <Status kind="warn">
            Meses_Construccion = {fmtNum(mesCOD, 0)} ≠ mes de COD del cronograma del libro ({fmtNum(maxFin, 0)})
          </Status>
        )}
      </ViewHeader>

      {/* Gantt */}
      <Section
        title="Cronograma a COD"
        guide={`un cuadro = un mes desde ${monthLabel(1)} · clic en una fila para verla en la tabla`}
        aside={
          <span className="text-[11.5px] text-ink-3">
            {fmtNum(nCrit, 0)} hitos en ruta crítica · {fmtNum(nParcial, 0)} parcial · {fmtNum(rows.length - nCrit - nParcial, 0)} no críticos
          </span>
        }
      >
        <Gantt rows={gantt} months={months} monthLabel={monthLabel} markers={markers} window={win} selected={sel} onSelect={setSel} />
        <p className="text-[11.5px] text-ink-3">
          Leyenda: barra en acento = ruta crítica · gris = no crítica («Parcial» se dibuja como no crítica y se indica en la tabla) · sombreado = vigencia de la
          Factibilidad de Conexión ({VIGENCIA_FACTIBILIDAD} meses desde el fin de RC-09{win ? `: meses ${fmtNum(win.from, 0)}–${fmtNum(win.to, 0)}, ${monthLabel(win.from)} → ${monthLabel(win.to)}` : ""}) · línea
          discontinua = COD
        </p>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          {f12Text && (
            <Status kind={statusOf(f12Text)}>
              <span title={f12Ctl?.desc}>Control F12 · {stripGlyph(f12Text)}</span>
              <Frozen what="Cronograma (fin de RC-09 y RC-10)" />
              <Trace name="Fin_RC09 · Fin_RC10" cell="13_Controles · F12" />
            </Status>
          )}
          <Chip title="01_Supuestos · Tol_Dias_COD">Tol_Dias_COD · {fmtNum(tolDias, 0)} días</Chip>
          {diffDias !== null && <span className="text-[11.5px] text-ink-3">COD implícito frente a Fecha_COD: {fmtNum(diffDias, 0)} días</span>}
        </div>
        {T.gantt_leyenda[1] && <Note>{T.gantt_leyenda[1]}</Note>}
      </Section>

      {/* tabla de hitos */}
      <Section title="Hitos" guide={`${fmtNum(rows.length, 0)} filas RC-xx con las columnas de la hoja · clic en una fila para resaltarla en el Gantt`}>
        <DataTable<Hito>
          columns={columns}
          rows={rows}
          rowKey={(r) => r.id}
          size="sm"
          selected={(r) => r.id === sel}
          onRowClick={(r) => setSel(sel === r.id ? null : r.id)}
          footer={`Hoja 03_Tramites, filas 8–24, columnas B–M; inicio, duración y costo son los del libro ${version} (${corte}). Meses contados desde ${monthLabel(1)}.`}
        />
      </Section>

      {/* totales (filas 25–27) */}
      <Section title="Costos de desarrollo frente al rubro 9 del CAPEX" guide={`el rubro 9 es el del caso seleccionado (${c.name}); la tolerancia es Tol_Costo_Tramites de 01 §I`}>
        <dl className="grid gap-x-8 gap-y-3 md:grid-cols-3">
          <div className="flex flex-col gap-1 border-t border-hairline pt-2">
            <dt className="text-[11.5px] text-ink-2">{lbl("25", "Costos de desarrollo y permisos (sin terreno; sin construcción)")}</dt>
            <dd className="flex flex-wrap items-baseline gap-x-2">
              <span className="text-[22px] font-semibold leading-none tracking-[-0.01em] text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>
                {fmtUSD(sumCostos)}
                <Frozen what="Cronograma valorado" />
              </span>
              <Trace name="Costo_Desarrollo_Cron" cell="03_Tramites!I25" />
            </dd>
          </div>
          <div className="flex flex-col gap-1 border-t border-hairline pt-2">
            <dt className="text-[11.5px] text-ink-2">{lbl("26", "Rubro 9 del CAPEX (desarrollo, permisos e ingeniería) — caso activo, cargado a GPM")}</dt>
            <dd className="flex flex-wrap items-baseline gap-x-2">
              <span className="text-[22px] font-semibold leading-none tracking-[-0.01em] text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>{fmtUSD(rubro9)}</span>
              <Trace cell="05_CAPEX!F15" />
            </dd>
            <span className="text-[11px] text-ink-3">
              caso {c.name} · ×(1 + {fmtPct(tol, 1)}) = {fmtUSD(rubro9 * (1 + tol))}
            </span>
          </div>
          <div className="flex flex-col gap-1 border-t border-hairline pt-2">
            <dt className="text-[11.5px] text-ink-2">{lbl("27", "Control: el cronograma valorado cabe en el rubro 9")}</dt>
            <dd className="flex flex-col gap-1">
              <Status kind={statusOf(cabeText)} className="text-[13px]">
                {stripGlyph(cabeText)}
                <Trace name="Check_Tramites" cell="03_Tramites!I27" />
              </Status>
              <span className="text-[11px] text-ink-3" style={{ fontVariantNumeric: "tabular-nums" }}>
                margen {fmtUSD(margen)} · Tol_Costo_Tramites {fmtPct(tol, 1)}
              </span>
            </dd>
          </div>
        </dl>
        <Note>
          Los costos del cronograma son los del libro (el artefacto no edita los hitos); el rubro 9 cambia con el caso y con los Mandos, igual que en{" "}
          <button type="button" className="text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid" onClick={() => onNavigate("capex")}>
            CAPEX
          </button>
          .
        </Note>
      </Section>

      {/* memo estático (filas 32–36) */}
      <Section
        title={memoTitle}
        aside={
          <Status kind="info">
            memo estático del libro {version} ({corte}): sus cifras no se recalculan con los Mandos
            <Frozen what="Memo" />
          </Status>
        }
      >
        <div className="flex flex-col gap-2">
          {T.memo.slice(1).map((p, k) => (
            <Note key={k}>{p}</Note>
          ))}
        </div>
      </Section>
    </div>
  );
}
