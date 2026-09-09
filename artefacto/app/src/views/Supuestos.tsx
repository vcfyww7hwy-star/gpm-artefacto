import { useMemo, useState, type ReactNode } from "react";

import { DataTable, type Column } from "@/components/DataTable";
import { Frozen, Live, Trace } from "@/components/Live";
import { Status, StatusGlyph, stripGlyph } from "@/components/Status";
import { Note, Section, ViewHeader } from "@/components/ViewHeader";
import type { Inputs } from "@/engine";
import { isExterno } from "@/lib/edition";
import { EM_DASH, fmtDate, fmtNum, fmtPct, fmtX, roundTo } from "@/lib/format";
import { CASES, viewMeta, type CaseId, type ViewId } from "@/lib/views";
import { cn } from "@/lib/utils";
import { statusOf, type Escenario, type InputRow } from "@/model/book";
import type { Live as LiveText, Value } from "@/model/formula";
import { BASELINE_EXTRAS, useModel } from "@/model/store";

/**
 * Supuestos (hoja 01_Supuestos): la única vista editable además de Mandos. Recorre los nueve bloques A–I del libro y, para
 * cada nombre definido, la fila de `book.inputs.rows` (bloque B: `book.inputs.escenarios`, editable sólo en la columna Custom).
 * Editar = `m.setInput` si el nombre es una entrada del Motor, si no `m.setExtra`. Las entradas distintas del libro se pintan
 * en acento; «volver al libro» restaura la v3.1 entregada. Los cambios viven en la sesión (no se guardan).
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

// ------------------------------------------------------------------------------------------------ formato del libro
/** Decimales del código de formato Excel («0.00» → 2, «#,##0.0» → 1, «0%» → 0; sólo la primera sección). */
function fmtDecimals(fmt: string | null | undefined): number {
  if (!fmt) return 0;
  const first = fmt.split(";")[0].replace(/"[^"]*"/g, "");
  const m = /\.([0#]+)/.exec(first);
  return m ? m[1].length : 0;
}
const isPctFmt = (fmt: string | null | undefined) => !!fmt && fmt.split(";")[0].includes("%");
const isXFmt = (fmt: string | null | undefined) => !!fmt && /"x"/.test(fmt);
const isDateFmt = (fmt: string | null | undefined, unit: string | null | undefined) => unit === "fecha" || (!!fmt && /yyyy/i.test(fmt));

/** Valor del libro formateado según su `fmt`/`unit` (es-EC). Vacío → «vacío» (el libro deja la celda en blanco). */
function fmtBook(v: Value, fmt: string | null | undefined, unit?: string | null): string {
  if (v === null || v === undefined || v === "") return "vacío";
  if (Array.isArray(v)) return fmtBook(v[0] ?? null, fmt, unit);
  if (typeof v === "boolean") return v ? "Sí" : "No";
  if (typeof v === "string") return isDateFmt(fmt, unit) ? fmtDate(v) : v;
  if (isPctFmt(fmt)) return fmtPct(v, fmtDecimals(fmt));
  if (isXFmt(fmt)) return fmtX(v, fmtDecimals(fmt));
  if (isDateFmt(fmt, unit)) return fmtDate(v);
  return fmtNum(v, fmtDecimals(fmt));
}

/** Paso del `<input type="number">`: porcentajes se editan en % con dos decimales; el resto según los decimales del formato. */
function stepOf(fmt: string | null | undefined): number {
  if (isPctFmt(fmt)) return 0.01;
  const d = fmtDecimals(fmt);
  return d > 0 ? Number(`1e-${d}`) : 1;
}

type Kind = "calc" | "info" | "yesno" | "selector" | "date" | "text" | "number";
function kindOf(row: InputRow): Kind {
  if (row.calc) return "calc";
  if (row.info) return "info";
  if (row.yesno) return "yesno";
  if (row.selector && row.selector.length > 0) return "selector";
  if (isDateFmt(row.fmt, row.unit)) return "date";
  if (row.unit === "texto" || (typeof row.value === "string" && !row.fmt)) return "text";
  return "number";
}

/** Hoja del libro → vista del artefacto (para «Sensibilizado en» y enlaces del libro). */
const SHEET_VIEW: Record<string, ViewId> = {
  "01_Supuestos": "supuestos", "02_Legal": "legal", "03_Tramites": "tramites", "04_Energia": "energia", "05_CAPEX": "capex",
  "06_OPEX": "opex", "07_Fiscal": "fiscal", "08_Flujo": "flujo", "09_Exergy": "exergy", "10_Sensibilidad": "sensibilidad",
  "11_Riesgos": "riesgos", "12_Fuentes": "fuentes", "13_Controles": "controles", Motor_Sens: "sensibilidad",
};
/** Ancla de «Sensibilizado en» → vista destino (sección de 10 → Sensibilidad; «#'Hoja'!Celda» → la vista de esa hoja). */
function viewForAnchor(anchor: string | null | undefined): ViewId | null {
  if (!anchor) return null;
  if (!anchor.startsWith("#")) return "sensibilidad";
  const m = /^#'([^']+)'!/.exec(anchor);
  const v = m ? SHEET_VIEW[m[1]] ?? null : null;
  // la vista Exergy es interna: en la edición externa no se enlaza
  return v === "exergy" && isExterno() ? null : v;
}

/** Columna H del bloque B (01_Supuestos!H38:H45, texto del libro): dónde se sensibiliza cada fila del escenario. */
const SENS_BLOQUE_B: Record<string, string> = {
  Escenario_Energia: "10 §A los cuatro casos · §A.2 P50 vs P90",
  Factor_CAPEX: "10 §A · §B CAPEX ± · §C matriz",
  CAPEX_Fijo_Wp: "10 §A (Favorable) · 05 comparativo",
  Factor_OPEX: "10 §A · §B OPEX ±",
  Peaje_SGDA: "10 §A · §B peaje · §E piso",
  Escalacion_Tarifa: "10 §A (Favorable) · §B escalación",
  Disponibilidad: "10 §A · §A.3 puente · §B ±2 pp",
  Escalacion_CAPEX: "10 §A · §A.3 puente · §B +2 pp · 05",
};

const rowId = (name: string) => `sup-${name}`;

// ------------------------------------------------------------------------------------------------ controles de edición
const INPUT_CLS =
  "h-7 rounded-1 border border-hairline bg-surface px-1.5 text-[12px] text-ink outline-none focus:border-accent disabled:text-ink-3";

function NumberField({ value, pct, step, nullable, dirty, placeholder, label, onCommit }: { value: number | null; pct: boolean; step: number; nullable: boolean; dirty: boolean; placeholder?: string; label: string; onCommit: (v: number | null) => void }) {
  const shown = value === null ? "" : String(pct ? roundTo(value * 100, 6) : value);
  // borrador sólo mientras el campo tiene el foco; fuera de la edición se muestra siempre el valor del modelo (Mandos, «volver al libro»)
  const [draft, setDraft] = useState<string | null>(null);
  const commit = (t: string) => {
    if (t.trim() === "") {
      if (nullable) onCommit(null);
      return;
    }
    const n = Number(t.replace(",", "."));
    if (!Number.isFinite(n)) return;
    onCommit(pct ? roundTo(n / 100, 10) : n);
  };
  return (
    <span className="inline-flex items-center gap-1">
      <input
        type="number"
        inputMode="decimal"
        step={step}
        value={draft ?? shown}
        placeholder={placeholder}
        aria-label={pct ? `${label} (%)` : label}
        onFocus={() => setDraft(shown)}
        onBlur={() => setDraft(null)}
        onChange={(e) => {
          setDraft(e.target.value);
          commit(e.target.value);
        }}
        className={cn(INPUT_CLS, "w-[112px] text-right", dirty && "border-accent/60 text-accent")}
        style={{ fontVariantNumeric: "tabular-nums" }}
      />
      {pct && <span className="w-3 text-[11px] text-ink-3">%</span>}
    </span>
  );
}

function TextField({ value, dirty, label, onCommit }: { value: string; dirty: boolean; label: string; onCommit: (v: string) => void }) {
  const [draft, setDraft] = useState<string | null>(null);
  return (
    <input
      type="text"
      value={draft ?? value}
      aria-label={label}
      onFocus={() => setDraft(value)}
      onBlur={() => setDraft(null)}
      onChange={(e) => {
        setDraft(e.target.value);
        if (e.target.value.trim() !== "") onCommit(e.target.value);
      }}
      className={cn(INPUT_CLS, "w-[112px] text-right", dirty && "border-accent/60 text-accent")}
    />
  );
}

/** Fecha ISO («YYYY-MM-DD»); no controlado (clave = valor) para no interferir con la edición por segmentos del navegador. */
function DateField({ value, dirty, label, onCommit }: { value: string; dirty: boolean; label: string; onCommit: (v: string) => void }) {
  return (
    <input
      key={value}
      type="date"
      defaultValue={value}
      aria-label={label}
      onChange={(e) => {
        const v = e.target.value;
        if (/^\d{4}-\d{2}-\d{2}$/.test(v)) onCommit(v);
      }}
      className={cn(INPUT_CLS, "w-[148px]", dirty && "border-accent/60 text-accent")}
    />
  );
}

function Segmented({ value, options, labels, dirty, label, onChange }: { value: string; options: readonly string[]; labels?: (o: string) => string; dirty: boolean; label: string; onChange: (v: string) => void }) {
  return (
    <div role="radiogroup" aria-label={label} className={cn("inline-flex h-7 items-stretch rounded-1 border border-hairline bg-surface p-px", dirty && "border-accent/60")}>
      {options.map((o) => (
        <button
          key={o}
          type="button"
          role="radio"
          aria-checked={o === value}
          onClick={() => onChange(o)}
          className={cn("rounded-[3px] px-2 text-[12px] text-ink-2 hover:text-ink", o === value && "bg-accent-soft font-medium text-accent")}
        >
          {labels ? labels(o) : o}
        </button>
      ))}
    </div>
  );
}

/** Cabecera de columna de caso: muestra de trazo (color/patrón del caso) + nombre. */
function CaseHead({ caseId }: { caseId: CaseId }) {
  const meta = CASES.find((c) => c.id === caseId)!;
  return (
    <span className="inline-flex items-center gap-1.5">
      <svg width="14" height="6" viewBox="0 0 14 6" aria-hidden>
        <line x1="0" y1="3" x2="14" y2="3" strokeWidth="2" style={{ stroke: `var(${meta.colorVar})`, strokeDasharray: `var(${meta.dashVar})` }} />
      </svg>
      {meta.label}
    </span>
  );
}

// ------------------------------------------------------------------------------------------------ vista
export function Supuestos({ onNavigate }: Props) {
  const m = useModel();
  const book = m.book;
  const rows = book.inputs.rows;
  const byName = useMemo(() => new Map(rows.filter((r) => r.name).map((r) => [r.name as string, r])), [rows]);
  const escByName = useMemo(() => new Map(book.inputs.escenarios.map((e) => [e.name, e])), [book]);
  const [openNotes, setOpenNotes] = useState<Set<string>>(() => new Set());
  const [notesBlock, setNotesBlock] = useState<Set<string>>(() => new Set());
  const toggleNote = (name: string) =>
    setOpenNotes((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  const toggleBlockNotes = (title: string) =>
    setNotesBlock((prev) => {
      const next = new Set(prev);
      if (next.has(title)) next.delete(title);
      else next.add(title);
      return next;
    });

  const inInputs = (name: string) => name in m.inputs;
  const isDirty = (name: string) => m.dirtyKeys.includes(name as keyof Inputs) || m.dirtyExtras.includes(name);
  const current = (name: string): Value =>
    inInputs(name) ? (m.inputs as unknown as Record<string, Value>)[name] : name in m.extras ? m.extras[name] : m.nameValue(name);
  const baselineOf = (name: string): Value =>
    inInputs(name) ? (m.baseline as unknown as Record<string, Value>)[name] : (BASELINE_EXTRAS[name] ?? null);
  const save = (name: string, v: Value) => {
    if (inInputs(name)) m.setInput(name as keyof Inputs, v as Inputs[keyof Inputs]);
    else m.setExtra(name, v);
  };
  const resetOne = (name: string) => save(name, baselineOf(name));
  // bloque B: sólo la columna Custom ([0]) se edita; se guarda una copia del arreglo
  const escArray = (esc: Escenario): Value[] => (m.inputs[esc.esc_name as keyof Inputs] as unknown as Value[]) ?? [];
  const saveEsc = (esc: Escenario, v: Value) => {
    const arr = [...escArray(esc)];
    arr[0] = v;
    m.setInput(esc.esc_name as keyof Inputs, arr as unknown as Inputs[keyof Inputs]);
  };
  const escDirty = (esc: Escenario) => m.dirtyKeys.includes(esc.esc_name as keyof Inputs);
  const escBaseline = (esc: Escenario): Value => ((m.baseline[esc.esc_name as keyof Inputs] as unknown as Value[]) ?? [])[0] ?? null;

  const scrollTo = (name: string) => document.getElementById(rowId(name))?.scrollIntoView({ behavior: "smooth", block: "center" });

  // estado del libro (filas 16–18 de 01): Estado_Custom lo calcula el motor; los demás son valores del libro (congelados)
  const estadoChip = (name: string, what: string) => {
    const s = String(m.nameValue(name) ?? "");
    if (!s) return null;
    const frozen = m.resolver.frozenUsed.has(name);
    return (
      <Status key={name} kind={statusOf(s)}>
        {stripGlyph(s)}
        {frozen && <Frozen what={what} />}
      </Status>
    );
  };
  const nConf = book.frozen.N_Por_Confirmar as number;
  const marcados = rows.filter((r) => r.name && r.confirm).length + book.inputs.escenarios.filter((e) => e.confirm).length;
  const esperados = book.inputs.n_por_confirmar_esperado;

  // ---------------------------------------------------------------------------------------------- celdas
  const editor = (row: InputRow): ReactNode => {
    const name = row.name as string;
    const kind = kindOf(row);
    const v = current(name);
    const dirty = isDirty(name);
    const label = row.label ?? name;
    if (kind === "calc") {
      return (
        <span className="text-ink-3" title="Calculado por el motor (no editable)" style={{ fontVariantNumeric: "tabular-nums" }}>
          {fmtBook(v, row.fmt, row.unit)}
        </span>
      );
    }
    if (kind === "info") {
      return (
        <span className="text-ink-2" title="Informativo: no alimenta cálculos" style={{ fontVariantNumeric: "tabular-nums" }}>
          {fmtBook(v, row.fmt, row.unit)}
        </span>
      );
    }
    if (kind === "yesno") return <Segmented value={String(v ?? "")} options={["Sí", "No"]} dirty={dirty} label={label} onChange={(o) => save(name, o)} />;
    if (kind === "selector") {
      const numeric = typeof v === "number" || typeof row.value === "number";
      return (
        <Segmented
          value={String(v ?? "")}
          options={row.selector as string[]}
          labels={numeric ? (o) => fmtNum(Number(o), 0) : undefined}
          dirty={dirty}
          label={label}
          onChange={(o) => save(name, numeric ? Number(o) : o)}
        />
      );
    }
    if (kind === "date") return <DateField value={typeof v === "string" ? v : ""} dirty={dirty} label={label} onCommit={(iso) => save(name, iso)} />;
    if (kind === "text") return <TextField value={typeof v === "string" ? v : ""} dirty={dirty} label={label} onCommit={(t) => save(name, t)} />;
    return (
      <NumberField
        value={typeof v === "number" ? v : null}
        pct={isPctFmt(row.fmt)}
        step={stepOf(row.fmt)}
        nullable={baselineOf(name) === null}
        dirty={dirty}
        placeholder={baselineOf(name) === null ? "vacío" : undefined}
        label={label}
        onCommit={(n) => save(name, n)}
      />
    );
  };

  /** Valor + «libro: …» y ↺ cuando la entrada difiere de la v3.1 entregada. */
  const valueCell = (name: string, field: ReactNode, dirty: boolean, baseline: Value, fmt: string | null | undefined, unit: string | null | undefined, reset: () => void) => (
    <div className="flex flex-col items-end gap-0.5">
      {field}
      {dirty && (
        <span className="inline-flex items-center gap-1 text-[10.5px] text-ink-3">
          libro: <span className="text-ink-2">{fmtBook(baseline, fmt, unit)}</span>
          <button type="button" className="text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid" onClick={reset} title={`Volver al valor del libro para ${name}`}>
            ↺
          </button>
        </span>
      )}
    </div>
  );

  const nameCell = (name: string, label: string, sub: LiveText | undefined, label2: string | null | undefined, note: LiveText | undefined, dirty: boolean, blockTitle: string) => {
    const open = openNotes.has(name) || notesBlock.has(blockTitle);
    return (
      <div className="flex flex-col gap-0.5">
        <span id={rowId(name)} className={cn("text-ink", dirty && "text-accent")}>{label}</span>
        {sub ? <Live text={sub} className="text-[11px] text-ink-3" /> : label2 ? <span className="text-[11px] text-ink-3">{label2}</span> : null}
        {open && note && <Live text={note} className="mt-1 max-w-[72ch] font-serif text-[12.5px] leading-[1.45] text-ink-2" />}
      </div>
    );
  };

  const noteCell = (name: string, note: LiveText | undefined, blockTitle: string) => {
    if (!note) return <span className="text-ink-3">{EM_DASH}</span>;
    const open = openNotes.has(name) || notesBlock.has(blockTitle);
    return (
      <button
        type="button"
        onClick={() => toggleNote(name)}
        title={m.live(note)}
        aria-expanded={open}
        className={cn("text-[11px] underline decoration-dotted underline-offset-2 hover:text-ink", open ? "text-ink" : "text-ink-2")}
      >
        nota {open ? "▴" : "▾"}
      </button>
    );
  };

  const confirmCell = (confirm: boolean | undefined, why: string | null | undefined) =>
    confirm ? (
      <span title={why ? `Por confirmar: ${why}` : "Por confirmar (sin fuente firme)"} className="inline-flex cursor-help items-center">
        <StatusGlyph kind="warn" className="text-[10px]" />
      </span>
    ) : null;

  const sensCell = (sens: [string, string] | null | undefined) => {
    if (!sens || !sens[0]) return <span className="text-ink-3">{EM_DASH}</span>;
    const target = viewForAnchor(sens[1]);
    if (!target) return <span className="text-ink-2">{sens[0]}</span>;
    return (
      <button type="button" onClick={() => onNavigate(target)} className="text-left text-ink-2 underline decoration-dotted underline-offset-2 hover:text-accent" title={`Abrir la vista ${viewMeta(target).label}`}>
        {sens[0]}
      </button>
    );
  };

  // ---------------------------------------------------------------------------------------------- columnas
  const columnsFor = (blockTitle: string): Column<InputRow>[] => [
    {
      key: "param",
      label: "Parámetro",
      width: "34%",
      render: (r) => nameCell(r.name as string, r.label ?? (r.name as string), r.short, r.label2, r.note, isDirty(r.name as string), blockTitle),
    },
    {
      key: "valor",
      label: "Valor",
      align: "right",
      width: "190px",
      render: (r) => {
        const name = r.name as string;
        const k = kindOf(r);
        const editable = k !== "calc" && k !== "info";
        return valueCell(name, editor(r), editable && isDirty(name), baselineOf(name), r.fmt, r.unit, () => resetOne(name));
      },
    },
    { key: "unidad", label: "Unidad", muted: true, nowrap: true, render: (r) => r.unit ?? "" },
    { key: "conf", label: "▲", title: "Por confirmar (sin fuente firme)", align: "center", width: "36px", render: (r) => confirmCell(r.confirm, r.confirm_why) },
    { key: "sens", label: "Sensibilizado en", width: "18%", render: (r) => sensCell(r.sens) },
    { key: "nota", label: "Nota", align: "center", width: "56px", render: (r) => noteCell(r.name as string, r.note, blockTitle) },
    { key: "ref", label: "Nombre", mono: true, render: (r) => <Trace name={r.name} /> },
  ];

  const escColumns = (blockTitle: string): Column<Escenario>[] => {
    const fixed = (idx: 1 | 2 | 3, key: "C" | "B" | "F"): ((e: Escenario) => ReactNode) => (e) => {
      const arr = escArray(e);
      const v = arr[idx] ?? null;
      const delivered = e.values[key];
      const differs = JSON.stringify(v) !== JSON.stringify(delivered);
      return (
        <span
          className={cn(differs ? "text-accent" : "text-ink-2", v === null && "text-ink-3")}
          title={differs ? `Definición entregada: ${fmtBook(delivered, e.fmt, e.unit)} (control G4)` : "Sólo lectura: definición entregada del caso"}
          style={{ fontVariantNumeric: "tabular-nums" }}
        >
          {fmtBook(v, e.fmt, e.unit)}
        </span>
      );
    };
    return [
      {
        key: "param",
        label: "Parámetro",
        width: "26%",
        render: (e) => nameCell(e.name, e.label, undefined, null, e.note, escDirty(e), blockTitle),
      },
      {
        key: "custom",
        label: <CaseHead caseId="custom" />,
        align: "right",
        width: "170px",
        render: (e) => {
          const v = escArray(e)[0] ?? null;
          const dirty = escDirty(e);
          const field =
            e.name === "Escenario_Energia" ? (
              <Segmented value={String(v ?? "")} options={["P50", "P90"]} dirty={dirty} label={`${e.label} · Custom`} onChange={(o) => saveEsc(e, o)} />
            ) : (
              <NumberField
                value={typeof v === "number" ? v : null}
                pct={isPctFmt(e.fmt)}
                step={stepOf(e.fmt)}
                nullable={escBaseline(e) === null}
                dirty={dirty}
                placeholder={escBaseline(e) === null ? "vacío" : undefined}
                label={`${e.label} · Custom`}
                onCommit={(n) => saveEsc(e, n)}
              />
            );
          return valueCell(e.name, field, dirty, escBaseline(e), e.fmt, e.unit, () => saveEsc(e, escBaseline(e)));
        },
      },
      { key: "C", label: <CaseHead caseId="conservador" />, align: "right", nowrap: true, render: fixed(1, "C") },
      { key: "B", label: <CaseHead caseId="base" />, align: "right", nowrap: true, render: fixed(2, "B") },
      { key: "F", label: <CaseHead caseId="favorable" />, align: "right", nowrap: true, render: fixed(3, "F") },
      { key: "unidad", label: "Unidad", muted: true, nowrap: true, render: (e) => e.unit ?? "" },
      { key: "conf", label: "▲", title: "Por confirmar (sin fuente firme)", align: "center", width: "36px", render: (e) => confirmCell(e.confirm, null) },
      { key: "sens", label: "Sensibilizado en", width: "16%", render: (e) => sensCell([SENS_BLOQUE_B[e.name] ?? "", "A"]) },
      { key: "nota", label: "Nota", align: "center", width: "56px", render: (e) => noteCell(e.name, e.note, blockTitle) },
      { key: "ref", label: "Nombre", mono: true, render: (e) => <Trace name={e.esc_name} /> },
    ];
  };

  const notesToggle = (title: string) => (
    <button type="button" onClick={() => toggleBlockNotes(title)} className="text-[11.5px] text-ink-3 underline decoration-dotted underline-offset-2 hover:text-ink">
      {notesBlock.has(title) ? "ocultar notas" : "mostrar notas"}
    </button>
  );

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="Supuestos" sheet="01_Supuestos">
        {estadoChip("Estado_Custom", "Estado")}
        {estadoChip("Estado_Entregado", "Estado")}
        {estadoChip("Estado_Controles", "Estado")}
        {estadoChip("Estado_Neutro", "Estado")}
        <Status kind="warn">
          {nConf} supuestos por confirmar (lista en{" "}
          <button type="button" className="underline decoration-dotted underline-offset-2 hover:text-ink" onClick={() => onNavigate("fuentes")}>12 §A</button>)
          <Frozen what="Conteo" />
        </Status>
        {m.dirty > 0 ? (
          <Status kind="info">
            sandbox: {m.dirty} entrada{m.dirty > 1 ? "s" : ""} distinta{m.dirty > 1 ? "s" : ""} del libro ·{" "}
            <button type="button" className="underline decoration-dotted underline-offset-2 hover:text-ink" onClick={m.reset}>volver al libro</button>
          </Status>
        ) : (
          <Status kind="ok">valores del libro {book.meta.version} ({fmtDate(book.meta.fecha_analisis)})</Status>
        )}
      </ViewHeader>

      <p className="-mt-4 max-w-[92ch] text-[12px] text-ink-3">
        Acento = editable y distinto del libro (aparece «libro: …» y ↺ para volver); tinta terciaria = calculado por el motor; ▲ = por confirmar (sin fuente firme).
        Cada cambio recalcula los {m.cases.length} casos; los valores viven en esta sesión y no se guardan.
      </p>

      {/* panel de mandos (filas 7–15 de 01) */}
      <Section title="Panel de mandos" guide={book.sheets["01_Supuestos"]?.labels["7"] ?? undefined}>
        <div className="grid grid-cols-2 gap-x-8 gap-y-5 lg:grid-cols-4">
          {book.inputs.panel.map((p) => (
            <div key={p.label} className="flex min-w-0 flex-col gap-1 border-t border-hairline pt-2">
              <span className="text-[10.5px] font-medium uppercase leading-tight tracking-[0.06em] text-ink-3">{p.label}</span>
              <div className={cn("text-[22px] font-semibold leading-tight tracking-[-0.01em]", p.extra ? "text-accent" : "text-ink")} style={{ fontVariantNumeric: "tabular-nums" }}>
                <Live text={p.value} />
              </div>
              <Live text={p.sub} className="text-[12px] text-ink-2" />
              <div className="mt-0.5 flex items-center justify-between gap-2">
                <Trace name={p.name} />
                <button type="button" onClick={() => scrollTo(p.name)} className="text-[11px] text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid">
                  editar ↓
                </button>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* bloques A–I */}
      {book.inputs.bloques.map((bl) => {
        const isB = bl.names.some((n) => escByName.has(n));
        if (isB) {
          const escs = bl.names.map((n) => escByName.get(n)).filter((e): e is Escenario => !!e);
          return (
            <Section key={bl.title} id={`bloque-${bl.title.charAt(0)}`} title={bl.title} guide={bl.guide} aside={notesToggle(bl.title)}>
              <DataTable<Escenario> columns={escColumns(bl.title)} rows={escs} rowKey={(e) => e.name} size="sm" />
            </Section>
          );
        }
        const blockRows = bl.names.map((n) => byName.get(n)).filter((r): r is InputRow => !!r);
        return (
          <Section key={bl.title} id={`bloque-${bl.title.charAt(0)}`} title={bl.title} guide={bl.guide} aside={notesToggle(bl.title)}>
            <DataTable<InputRow> columns={columnsFor(bl.title)} rows={blockRows} rowKey={(r) => r.name as string} size="sm" />
          </Section>
        );
      })}

      {/* por confirmar (12 §A) */}
      <Section
        title="Por confirmar"
        guide="Marcados aquí + los drivers de escala de 05 (un ítem); lista en 12 §A"
        aside={
          <Status kind={marcados === esperados ? "ok" : "warn"}>
            {marcados} marcadas en esta hoja frente a {esperados} esperadas al entregar · {nConf} en el libro (con los drivers de 05)
            <Frozen what="Conteo" />
          </Status>
        }
      >
        <ul className="flex flex-col divide-y divide-hairline">
          {book.inputs.confirm_list.map((t, k) => {
            const informative = /^(Además \(no contados\)|Pendientes legales)/.test(t);
            return (
              <li key={k} className="grid grid-cols-[16px_minmax(0,1fr)] items-start gap-x-2 py-1.5 font-serif text-[13px] leading-[1.45] text-ink-2">
                <StatusGlyph kind={informative ? "info" : "warn"} className="mt-1.5" />
                <span>{t}</span>
              </li>
            );
          })}
        </ul>
        <Note>
          Las entradas marcadas ▲ no tienen fuente firme; la lista completa, con las simplificaciones declaradas y las fuentes, está en{" "}
          <button type="button" className="text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid" onClick={() => onNavigate("fuentes")}>Fuentes</button>.
        </Note>
      </Section>
    </div>
  );
}
