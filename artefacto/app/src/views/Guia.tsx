import type { ReactNode } from "react";

import { DataTable, type Column } from "@/components/DataTable";
import { Frozen, Live } from "@/components/Live";
import { StatusGlyph } from "@/components/Status";
import { Note, Section, ViewHeader } from "@/components/ViewHeader";
import { isExterno } from "@/lib/edition";
import { CASES, viewMeta, type CaseId, type ViewId } from "@/lib/views";
import type { Live as LiveText } from "@/model/formula";
import { useModel } from "@/model/store";

/**
 * Guía de lectura (hoja 00b_Guía): pasos, convenciones (el color del libro traducido a los tokens del artefacto), preguntas
 * frecuentes, glosario por grupos con su cifra viva e índice de hojas ↔ vistas. Todo el contenido sale de `book.guia`.
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

/** Hoja del libro → vista del artefacto. */
const SHEET_VIEW: Record<string, ViewId> = {
  "00_Portada": "resumen", "01_Supuestos": "supuestos", "02_Legal": "legal", "03_Tramites": "tramites", "04_Energia": "energia",
  "05_CAPEX": "capex", "06_OPEX": "opex", "07_Fiscal": "fiscal", "08_Flujo": "flujo", "09_Exergy": "exergy",
  "10_Sensibilidad": "sensibilidad", "11_Riesgos": "riesgos", "12_Fuentes": "fuentes", "13_Controles": "controles", Motor_Sens: "sensibilidad",
};

/** Pie de la hoja (00b_Guía!B92), misma fórmula del libro evaluada en vivo. */
const PIE: LiveText = [
  "tpl",
  [
    "Guía elaborada con el libro ",
    ["name", "Version"],
    " (",
    ["call", "TEXT", [["name", "Fecha_Analisis"], ["str", "dd-mmm-yyyy"]]],
    "). Documento de trabajo interno de Exergy EXG S.A.S.; no constituye oferta ni opinión legal.",
  ],
];

function CaseLine({ caseId }: { caseId: CaseId }) {
  const meta = CASES.find((c) => c.id === caseId)!;
  return (
    <svg width="28" height="6" viewBox="0 0 28 6" aria-hidden className="shrink-0">
      <line x1="0" y1="3" x2="28" y2="3" strokeWidth="2" style={{ stroke: `var(${meta.colorVar})`, strokeDasharray: `var(${meta.dashVar})` }} />
    </svg>
  );
}

/** Traducción de cada convención del libro (columna «a» de 00b) a los tokens del artefacto: muestra + texto. */
const EN_EL_ARTEFACTO: Record<string, { sample: ReactNode; text: string }> = {
  "texto en tinta": { sample: <span className="text-accent">texto en acento</span>, text: "acento: entradas editables (Supuestos y Mandos)" },
  "● ok · ▲ atención · ■ riesgo · ◇ informativo": {
    sample: (
      <span className="inline-flex flex-wrap items-center gap-x-2 text-ink-2">
        <span className="inline-flex items-center gap-1"><StatusGlyph kind="ok" /> ok</span>
        <span className="inline-flex items-center gap-1"><StatusGlyph kind="warn" /> atención</span>
        <span className="inline-flex items-center gap-1"><StatusGlyph kind="risk" /> riesgo</span>
        <span className="inline-flex items-center gap-1"><StatusGlyph kind="info" /> informativo</span>
      </span>
    ),
    text: "los mismos glifos; el color va sólo en el glifo, el texto en tinta",
  },
  "carbón · grafito · piedra": {
    sample: (
      <span>
        <span className="text-ink">tinta</span> · <span className="text-ink-2">tinta 2</span> · <span className="text-ink-3">tinta 3</span>
      </span>
    ),
    text: "tres tintas: texto y cifras · etiquetas y notas · pistas, ejes y valores calculados",
  },
  "«· por confirmar» (subrayado punteado)": {
    sample: (
      <span className="inline-flex items-center gap-1.5 text-ink-2">
        <StatusGlyph kind="warn" /> <span className="underline decoration-dotted underline-offset-2">por confirmar</span>
      </span>
    ),
    text: "▲ en la columna «por confirmar» de Supuestos, con el motivo al pasar el cursor",
  },
  terracota: { sample: <span className="text-accent underline decoration-dotted underline-offset-2">el dato que decide</span>, text: "acento: enlaces y el dato que decide" },
  "arcilla en 01": { sample: <span className="text-accent">≠ libro</span>, text: "acento en Supuestos: entrada distinta del libro (aparece «libro: …» y ↺)" },
  "ciruela · Custom": { sample: <span className="inline-flex items-center gap-2 text-ink-2"><CaseLine caseId="custom" /> Custom</span>, text: "acento, trazo continuo" },
  "fila bruma": {
    sample: <span className="rounded-[2px] bg-surface-2 px-1.5 py-0.5 text-[10.5px] font-medium uppercase tracking-[0.06em] text-ink-3">Sección</span>,
    text: "fila de sección en las tablas y cabecera de sección con su guía",
  },
  "índigo · Conservador": { sample: <span className="inline-flex items-center gap-2 text-ink-2"><CaseLine caseId="conservador" /> Conservador</span>, text: "gris oscuro, trazo discontinuo" },
  "+/− en columnas": { sample: <span className="text-ink-3">—</span>, text: "sin agrupación: las series anuales se muestran completas" },
  "petróleo · Base": { sample: <span className="inline-flex items-center gap-2 text-ink-2"><CaseLine caseId="base" /> Base</span>, text: "gris medio, trazo continuo" },
  "ladrillo / arcilla en cifras": { sample: <span className="text-risk">cifra bajo el umbral</span>, text: "rojo (riesgo) sólo en la cifra que queda bajo el umbral" },
  "verde bosque · Favorable": { sample: <span className="inline-flex items-center gap-2 text-ink-2"><CaseLine caseId="favorable" /> Favorable</span>, text: "gris claro, trazo punteado" },
  "toda cifra en texto es fórmula": {
    sample: <span className="text-ink-2">valor del libro<Frozen what="Dato" /></span>,
    text: "el motor recalcula todo con cada cambio; lo que sólo existe en el libro (controles, conteos) lleva esta marca",
  },
};

interface Conv { a: string; b: string; color: string; bold: boolean }
interface Term { term: string; def: LiveText; live: LiveText; anchor: string | null }

export function Guia({ onNavigate }: Props) {
  const m = useModel();
  const g = m.book.guia;
  const labels = m.book.sheets["00b_Guía"]?.labels ?? {};
  const nTerms = g.grupos.reduce((n, gr) => n + gr.items.length, 0);

  const convColumns: Column<Conv>[] = [
    { key: "a", label: "En el libro", width: "26%", render: (c) => <span className={c.bold ? "font-medium text-ink" : "text-ink"}>{c.a}</span> },
    { key: "b", label: "Significado", width: "40%", render: (c) => <span className="text-ink-2">{c.b}</span> },
    {
      key: "art",
      label: "En el artefacto",
      render: (c) => {
        const t = EN_EL_ARTEFACTO[c.a];
        if (!t) return <span className="text-ink-3">—</span>;
        return (
          <span className="flex flex-col gap-0.5">
            <span>{t.sample}</span>
            <span className="text-[11px] text-ink-3">{t.text}</span>
          </span>
        );
      },
    },
  ];

  const termColumns: Column<Term>[] = [
    { key: "term", label: "Término", width: "20%", render: (t) => <span className="font-medium text-ink">{t.term}</span> },
    { key: "def", label: "Qué es y dónde vive", width: "40%", render: (t) => <Live text={t.def} className="text-ink-2" /> },
    { key: "live", label: "Cómo leerlo (cifra viva)", render: (t) => <Live text={t.live} className="text-ink" /> },
  ];

  /** Vista destino de una hoja; la vista Exergy es interna y en la edición externa no se enlaza. */
  const viewOf = (sheet: string): ViewId | null => {
    const v = SHEET_VIEW[sheet] ?? null;
    return v === "exergy" && isExterno() ? null : v;
  };

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="Guía de lectura" sheet="00b_Guía" />

      {/* 1 · pasos */}
      <Section title={labels["5"] ?? "1 · El libro en cinco minutos"} guide="qué calcula, cómo se lee, dónde se edita, dónde se decide y cómo se verifica">
        <ol className="grid gap-x-8 gap-y-4 md:grid-cols-2">
          {g.pasos.map((p) => {
            const v = viewOf(p.sheet);
            return (
              <li key={p.title} className="flex flex-col gap-1 border-t border-hairline pt-2">
                <span className="text-[13px] font-semibold text-ink">{p.title}</span>
                <Live text={p.text} className="font-serif text-[13.5px] leading-[1.45] text-ink-2" />
                {v && (
                  <button type="button" onClick={() => onNavigate(v)} className="self-start text-[12px] text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid">
                    → {viewMeta(v).label} <span className="font-mono text-[10.5px] text-ink-3">{p.sheet}</span>
                  </button>
                )}
              </li>
            );
          })}
        </ol>
      </Section>

      {/* 2 · convenciones */}
      <Section title={labels["12"] ?? "2 · Convenciones"} guide="el color sólo aparece con significado; todo lo demás es escala de grises">
        <DataTable<Conv> columns={convColumns} rows={g.convenciones} rowKey={(c) => c.a} />
      </Section>

      {/* 3 · preguntas frecuentes */}
      <Section title={labels["21"] ?? "3 · Preguntas frecuentes"} guide={`${g.faq.length} preguntas · cada respuesta señala la hoja donde se ve el dato · las cifras son las del momento`}>
        <div className="flex flex-col divide-y divide-hairline border-y border-hairline">
          {g.faq.map((f, k) => (
            <details key={k} className="group py-2">
              <summary className="flex cursor-pointer list-none items-start gap-2 text-[13px] font-medium text-ink hover:text-accent [&::-webkit-details-marker]:hidden">
                <span aria-hidden className="mt-[3px] w-3 shrink-0 text-[10px] text-ink-3 transition-transform group-open:rotate-90">▶</span>
                <Live text={f.q} />
              </summary>
              <Live text={f.a} className="mt-1.5 block max-w-[92ch] pl-5 font-serif text-[13.5px] leading-[1.5] text-ink-2" />
            </details>
          ))}
        </div>
      </Section>

      {/* 4 · glosario */}
      <Section title={labels["37"] ?? "4 · Glosario"} guide={`${nTerms} términos en ${g.grupos.length} grupos · la cifra viva cambia con Supuestos y Mandos`}>
        <div className="flex flex-col gap-6">
          {g.grupos.map((gr) => (
            <div key={gr.title} className="flex flex-col gap-2">
              <h3 className="text-[12px] font-medium text-ink-2">{gr.title}</h3>
              <DataTable<Term> columns={termColumns} rows={gr.items} rowKey={(t) => t.term} size="sm" />
            </div>
          ))}
        </div>
      </Section>

      {/* índice de hojas ↔ vistas */}
      <Section title="Índice de hojas" guide="cada hoja del libro y la vista del artefacto que la sustituye">
        <ul className="grid gap-x-8 gap-y-1 sm:grid-cols-2">
          {g.index.map((it) => {
            const v = viewOf(it.sheet);
            return (
              <li key={it.sheet} className="grid grid-cols-[132px_minmax(0,1fr)_auto] items-baseline gap-x-3 border-b border-hairline py-1.5 text-[12.5px]">
                <span className="font-mono text-[11px] text-ink-3">{it.sheet}</span>
                <span className="text-ink">{it.title}</span>
                {v ? (
                  <button type="button" onClick={() => onNavigate(v)} className="text-[12px] text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid">
                    {viewMeta(v).label} →
                  </button>
                ) : (
                  <span className="text-[12px] text-ink-3">—</span>
                )}
              </li>
            );
          })}
        </ul>
      </Section>

      <Note>
        <Live text={PIE} />
      </Note>
    </div>
  );
}
