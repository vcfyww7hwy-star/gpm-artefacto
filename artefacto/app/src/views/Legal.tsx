import { useMemo, useState, type ReactNode } from "react";

import { DataTable, type Column } from "@/components/DataTable";
import { Live, LiveStatus, Trace } from "@/components/Live";
import { Status, type StatusKind } from "@/components/Status";
import { Chip, Note, Section, ViewHeader } from "@/components/ViewHeader";
import { fmtNum } from "@/lib/format";
import type { CaseId, ViewId } from "@/lib/views";
import { cn } from "@/lib/utils";
import { statusOf, type Book } from "@/model/book";
import type { Live as LiveText, Node as AstNode } from "@/model/formula";
import { useModel } from "@/model/store";

/**
 * Marco legal y regulatorio (hoja 02_Legal): los cinco candados del régimen con su estado en vivo, la matriz normativa
 * verificada (25 normas, con filtro por confianza y búsqueda), la arquitectura contractual (8 instrumentos) y las zonas grises
 * (15 dudas con urgencia). Todos los textos son los del libro (book.json), evaluados con los valores actuales del motor;
 * el punto gris junto a un texto indica que depende de un valor que sólo existe en el libro.
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

type Norma = Book["legal"]["rows"][number];
type Contrato = Book["legal"]["contratos"][number];
type Duda = Book["legal"]["dudas"][number];

/** Fila de la matriz normativa ya evaluada (para buscar y filtrar sobre lo que se ve). */
interface NormaRow {
  k: number;
  r: Norma;
  texto: string;
  haystack: string;
}

/** Niveles de confianza que puede mencionar la celda G de la hoja («Alta / Media (red)» cuenta en Alta y en Media). */
const CONF_LEVELS = ["Alta", "Media", "Baja", "❓"] as const;
type ConfLevel = (typeof CONF_LEVELS)[number];

/** A partir de esta longitud la columna «Qué dice (verificado)» se pliega a dos líneas con «ver más». */
const CLAMP_CHARS = 150;

/** Búsqueda sin acentos ni mayúsculas. */
const norm = (s: string) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

/**
 * Fórmulas de texto de 02_Legal que book.json entrega como cadena («="…"&TEXT(Nombre,"fmt")&"…"»): el criterio de los candados
 * 4 y 5 (C10, C11) y el título del contrato de arriendo (B45). Se transcriben al AST del evaluador para que digan lo que dice
 * el Excel con las cifras del momento. Cubre literales, nombres y TEXT(expr,"fmt") con expr = nombre u operación simple
 * (nombre * / + − número); si algo no encaja, se devuelve la cadena tal cual.
 */
function concatFormula(l: LiveText): LiveText {
  if (typeof l !== "string") return l;   // el extractor (book.json) ya entrega el AST vivo
  const s = l;
  if (!s.startsWith("=")) return s;
  const n = s.length;
  let i = 1;
  const skipWs = () => {
    while (i < n && s[i] === " ") i++;
  };
  const readString = (): string | null => {
    let out = "";
    i++; // comilla de apertura
    while (i < n) {
      const ch = s[i];
      if (ch === '"') {
        if (s[i + 1] === '"') { out += '"'; i += 2; continue; }
        i++;
        return out;
      }
      out += ch;
      i++;
    }
    return null;
  };
  const readIdent = (): string => {
    const m = /^[A-Za-z_][A-Za-z0-9_.]*/.exec(s.slice(i));
    if (!m) return "";
    i += m[0].length;
    return m[0];
  };
  const readOperand = (): AstNode | null => {
    skipWs();
    const num = /^\d+(\.\d+)?/.exec(s.slice(i));
    if (num) { i += num[0].length; return ["num", Number(num[0])]; }
    const id = readIdent();
    return id ? ["name", id] : null;
  };
  const readExpr = (): AstNode | null => {
    let left = readOperand();
    if (!left) return null;
    skipWs();
    while (i < n && "*/+-".includes(s[i])) {
      const op = s[i];
      i++;
      const right = readOperand();
      if (!right) return null;
      left = ["bin", op, left, right];
      skipWs();
    }
    return left;
  };
  const readTerm = (): string | AstNode | null => {
    skipWs();
    if (s[i] === '"') return readString();
    const id = readIdent();
    if (id.toUpperCase() === "TEXT" && s[i] === "(") {
      i++;
      const expr = readExpr();
      if (!expr) return null;
      skipWs();
      if (s[i] !== ",") return null;
      i++;
      skipWs();
      if (s[i] !== '"') return null;
      const fmt = readString();
      if (fmt === null) return null;
      skipWs();
      if (s[i] !== ")") return null;
      i++;
      return ["call", "TEXT", [expr, ["str", fmt]]];
    }
    return id ? ["name", id] : null;
  };
  const parts: (string | AstNode)[] = [];
  while (i < n) {
    const t = readTerm();
    if (t === null) return s;
    parts.push(t);
    skipWs();
    if (i >= n) break;
    if (s[i] !== "&") return s;
    i++;
  }
  return ["tpl", parts];
}

/** Botón de filtro segmentado (mismo dibujo que en Controles). */
function Segmented<T extends string | boolean | null>({ value, options, onChange }: { value: T; options: { v: T; label: string }[]; onChange: (v: T) => void }) {
  return (
    <div role="radiogroup" className="inline-flex h-7 flex-wrap items-stretch rounded-1 border border-hairline bg-surface p-px">
      {options.map((o) => (
        <button
          key={String(o.v)}
          type="button"
          role="radio"
          aria-checked={value === o.v}
          onClick={() => onChange(o.v)}
          className={cn("rounded-[3px] px-2.5 text-[12px] text-ink-2 hover:text-ink", value === o.v && "bg-accent-soft font-medium text-accent")}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function ViewLink({ onClick, children }: { onClick: () => void; children: ReactNode }) {
  return (
    <button type="button" onClick={onClick} className="text-[12px] text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid">
      {children}
    </button>
  );
}

export function Legal({ onNavigate }: Props) {
  const m = useModel();
  const legal = m.book.legal;
  const labels = m.book.sheets["02_Legal"]?.labels ?? {};

  // --- filtros de la matriz normativa -------------------------------------------------------------------------------
  const [conf, setConf] = useState<ConfLevel | null>(null);
  const [q, setQ] = useState("");
  const [expanded, setExpanded] = useState<Set<number>>(() => new Set());
  const toggle = (k: number) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });

  const normas = useMemo<NormaRow[]>(
    () =>
      legal.rows.map((r, k) => {
        const texto = m.live(r.texto);
        const haystack = norm([m.live(r.tema), m.live(r.norma), texto, m.live(r.aplicacion), m.live(r.estado), m.live(r.confianza)].join(" · "));
        return { k, r, texto, haystack };
      }),
    [legal, m],
  );
  const confText = (r: { confianza: LiveText }) => m.live(r.confianza);
  const levels = useMemo(() => CONF_LEVELS.filter((l) => legal.rows.some((r) => confText(r).includes(l))), [legal, m]); // eslint-disable-line react-hooks/exhaustive-deps
  const countOf = (l: ConfLevel) => legal.rows.filter((r) => confText(r).includes(l)).length;
  const nq = norm(q.trim());
  const visibles = normas.filter((e) => (conf === null || confText(e.r).includes(conf)) && (nq === "" || e.haystack.includes(nq)));

  // --- candados ---------------------------------------------------------------------------------------------------------
  const candadoKinds = legal.candados.map((c) => statusOf(m.live(c.estado)));
  const nKind = (k: StatusKind) => candadoKinds.filter((x) => x === k).length;

  // --- dudas ------------------------------------------------------------------------------------------------------------
  const [soloAlta, setSoloAlta] = useState(false);
  const nAlta = legal.dudas.filter((d) => d.prioridad === "Alta").length;
  const dudas = soloAlta ? legal.dudas.filter((d) => d.prioridad === "Alta") : legal.dudas;

  // --- cabeceras de tabla (las de la hoja) --------------------------------------------------------------------------------
  const hMarco = legal.table_headers.marco ?? [];
  const hCand = legal.table_headers.candados ?? [];
  const hContr = legal.table_headers.contratos ?? [];
  const hDudas = legal.table_headers.dudas ?? [];
  const h = (arr: (string | null)[], k: number, fallback: string) => arr[k] ?? fallback;

  const colsMarco: Column<NormaRow>[] = [
    { key: "tema", label: h(hMarco, 0, "Tema"), width: "12%", render: (e) => <span className="font-medium text-ink">{e.r.tema}</span> },
    { key: "norma", label: h(hMarco, 1, "Norma / artículo"), width: "15%", render: (e) => <Live text={e.r.norma} className="text-ink-2" /> },
    {
      key: "texto",
      label: h(hMarco, 2, "Qué dice (verificado)"),
      width: "25%",
      render: (e) => {
        const open = expanded.has(e.k);
        const long = e.texto.length > CLAMP_CHARS;
        return (
          <div className="flex flex-col items-start gap-0.5">
            <div className={cn("text-ink-2", long && !open && "line-clamp-2")}>
              <Live text={e.r.texto} />
            </div>
            {long && (
              <button type="button" aria-expanded={open} onClick={() => toggle(e.k)} className="text-[11px] text-ink-3 underline decoration-dotted underline-offset-2 hover:text-ink">
                {open ? "ver menos" : "ver más"}
              </button>
            )}
          </div>
        );
      },
    },
    { key: "aplicacion", label: h(hMarco, 3, "Implicación para GPM / Exergy"), width: "27%", render: (e) => <Live text={e.r.aplicacion} className="text-ink" /> },
    { key: "estado", label: h(hMarco, 4, "Estado · verificación"), width: "13%", render: (e) => <Live text={e.r.estado} className="text-[11px] text-ink-3" /> },
    { key: "confianza", label: h(hMarco, 5, "Confianza"), width: "8%", render: (e) => <span className="text-ink-2">{e.r.confianza}</span> },
  ];

  const colsContratos: Column<Contrato>[] = [
    { key: "contrato", label: h(hContr, 0, "Instrumento"), width: "24%", render: (r) => <Live text={concatFormula(r.contrato)} className="font-medium text-ink" /> },
    { key: "partes", label: h(hContr, 1, "Partes"), width: "14%", nowrap: false, render: (r) => <span className="text-ink-2">{r.partes}</span> },
    { key: "alcance", label: h(hContr, 2, "Contenido esencial"), width: "36%", render: (r) => <Live text={r.alcance} className="text-ink" /> },
    { key: "nota", label: h(hContr, 3, "Nota"), width: "26%", render: (r) => <Live text={r.nota} className="text-ink-2" /> },
  ];

  const colsDudas: Column<Duda>[] = [
    { key: "id", label: h(hDudas, 0, "#"), mono: true, nowrap: true, width: "110px", render: (d) => <span className="text-ink-3">{d.id}</span> },
    { key: "duda", label: h(hDudas, 1, "Duda"), width: "34%", render: (d) => <Live text={d.duda} className="text-ink" /> },
    { key: "impacto", label: h(hDudas, 2, "Por qué importa"), width: "24%", render: (d) => <Live text={d.impacto} className="text-ink-2" /> },
    { key: "accion", label: h(hDudas, 3, "Resolver con"), width: "24%", render: (d) => <Live text={d.accion} className="text-ink-2" /> },
    {
      key: "prioridad",
      label: h(hDudas, 4, "Urgencia"),
      nowrap: true,
      width: "90px",
      render: (d) => <Status kind={d.prioridad === "Alta" ? "warn" : "info"}>{d.prioridad}</Status>,
    },
  ];

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="Marco legal y regulatorio" sheet="02_Legal">
        <Chip>{fmtNum(legal.rows.length, 0)} normas</Chip>
        <Chip>{fmtNum(legal.contratos.length, 0)} instrumentos</Chip>
        <Chip>
          {fmtNum(legal.dudas.length, 0)} zonas grises · {fmtNum(nAlta, 0)} en urgencia Alta
        </Chip>
        {nKind("ok") > 0 && <Status kind="ok">{fmtNum(nKind("ok"), 0)} candado{nKind("ok") === 1 ? "" : "s"} en ●</Status>}
        {nKind("warn") > 0 && <Status kind="warn">{fmtNum(nKind("warn"), 0)} en ▲</Status>}
        {nKind("risk") > 0 && <Status kind="risk">{fmtNum(nKind("risk"), 0)} en ■</Status>}
      </ViewHeader>

      {/* candados (filas 5–11) */}
      <Section title={labels["5"] ?? "Los 5 candados del régimen elegido (estado en vivo)"} guide="el estado se evalúa con los valores actuales del motor; el criterio es el de la hoja">
        <div className="text-[12.5px]">
          <div className="hidden border-b border-hairline pb-1.5 text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3 md:grid md:grid-cols-[minmax(0,2fr)_minmax(0,4fr)_minmax(0,5fr)] md:gap-x-4">
            <span>{h(hCand, 0, "Candado")}</span>
            <span>{h(hCand, 1, "Qué exige")}</span>
            <span>{h(hCand, 2, "Estado")}</span>
          </div>
          <ul className="flex flex-col divide-y divide-hairline">
            {legal.candados.map((c, k) => (
              <li key={k} className="grid gap-x-4 gap-y-1 py-2 md:grid-cols-[minmax(0,2fr)_minmax(0,4fr)_minmax(0,5fr)]">
                <span className="flex flex-col gap-0.5">
                  <span className="font-medium text-ink"><Live text={c.label} /></span>
                  <Trace cell={`02_Legal!D${7 + k}`} />
                </span>
                <span className="text-ink-2">
                  <Live text={concatFormula(c.criterio)} />
                </span>
                <LiveStatus text={c.estado} className="text-[12.5px]" />
              </li>
            ))}
          </ul>
        </div>
      </Section>

      {/* matriz normativa (filas 13–39) */}
      <Section
        title={labels["13"] ?? "Matriz normativa verificada"}
        guide={`${fmtNum(visibles.length, 0)} de ${fmtNum(normas.length, 0)} normas · el filtro toma cualquier mención de la celda de confianza («Alta / Media (red)» cuenta en Alta y en Media)`}
        aside={
          <div className="flex flex-wrap items-center gap-2">
            <Segmented<ConfLevel | null>
              value={conf}
              onChange={setConf}
              options={[{ v: null, label: `Todas (${fmtNum(normas.length, 0)})` }, ...levels.map((l) => ({ v: l as ConfLevel | null, label: `${l} (${fmtNum(countOf(l), 0)})` }))]}
            />
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar en la matriz…"
              aria-label="Buscar en la matriz normativa"
              className="h-7 w-[200px] rounded-1 border border-hairline bg-surface px-2 text-[12px] text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none"
            />
          </div>
        }
      >
        <DataTable<NormaRow>
          columns={colsMarco}
          rows={visibles}
          rowKey={(e) => String(e.k)}
          size="sm"
          footer="Hoja 02_Legal, filas 15–39, columnas B–G; textos tal cual, evaluados con los valores actuales. El punto gris marca un texto que depende de un valor que sólo existe en el libro."
        />
        {visibles.length === 0 && <p className="text-[12px] text-ink-3">Ninguna norma coincide con el filtro y la búsqueda.</p>}
      </Section>

      {/* contratos (filas 41–50) */}
      <Section title={labels["41"] ?? "Arquitectura contractual (SALELGI dueña · Exergy gerencia, arrienda y opera)"} guide="alcance y nota de cada instrumento con las cifras del momento (fee, $/kWp, renta, hectáreas)">
        <DataTable<Contrato> columns={colsContratos} rows={legal.contratos} rowKey={(_, i) => String(i)} size="sm" footer="Hoja 02_Legal, filas 43–50, columnas B–E." />
      </Section>

      {/* zonas grises (filas 52–68) */}
      <Section
        title={labels["52"] ?? "Zonas grises vivas (con dueño y urgencia) — dudas del Informe Maestro y pendientes P-xx del Atlas Regulatorio v2.0"}
        guide="▲ = urgencia Alta; el resto en ◇"
        aside={
          <Segmented<boolean>
            value={soloAlta}
            onChange={setSoloAlta}
            options={[
              { v: false, label: `Todas (${fmtNum(legal.dudas.length, 0)})` },
              { v: true, label: `Urgencia Alta (${fmtNum(nAlta, 0)})` },
            ]}
          />
        }
      >
        <DataTable<Duda> columns={colsDudas} rows={dudas} rowKey={(d) => `${d.id}-${legal.dudas.indexOf(d)}`} size="sm" footer="Hoja 02_Legal, filas 54–68, columnas B–F." />
      </Section>

      <Note>
        Vistas relacionadas: <ViewLink onClick={() => onNavigate("riesgos")}>Riesgos →</ViewLink> · <ViewLink onClick={() => onNavigate("tramites")}>Trámites →</ViewLink> ·{" "}
        <ViewLink onClick={() => onNavigate("fuentes")}>Fuentes →</ViewLink> · <ViewLink onClick={() => onNavigate("controles")}>Controles →</ViewLink>
      </Note>
    </div>
  );
}
