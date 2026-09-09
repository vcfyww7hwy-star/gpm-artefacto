import { useMemo, type ReactNode } from "react";

import { DataTable, type Column } from "@/components/DataTable";
import { Live } from "@/components/Live";
import { StatusGlyph } from "@/components/Status";
import { Note, Section, ViewHeader } from "@/components/ViewHeader";
import type { CaseId, ViewId } from "@/lib/views";
import type { CellRow } from "@/model/book";
import type { Live as LiveText, Value } from "@/model/formula";
import { useModel } from "@/model/store";

/**
 * Fuentes y calidad (hoja 12_Fuentes): las secciones A–E de la hoja reconstruidas desde `book.fuentes.cells` (columnas B–D),
 * agrupadas por las cabeceras de `book.fuentes.secciones`. §A usa `book.inputs.confirm_list`; §D usa `book.fuentes.rows`
 * (texto + enlace). Texto tal cual; las cuatro celdas que en el libro son fórmulas se evalúan en vivo con la misma fórmula.
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

/**
 * Celdas de 12_Fuentes que en el libro son fórmulas de texto (book.fuentes.cells[].f): transcritas al AST del evaluador para
 * que digan lo que dice el Excel con las cifras del momento (N_Por_Confirmar sólo existe en el libro → marca «valor del libro»).
 */
const LIVE_CELLS: Record<string, LiveText> = {
  // C5 ="marcados «· por confirmar» (subrayado punteado) en 01_Supuestos y en los drivers de 05_CAPEX · "&N_Por_Confirmar&" en el libro · control I2"
  C5: ["tpl", ["marcados «· por confirmar» (subrayado punteado) en 01_Supuestos y en los drivers de 05_CAPEX · ", ["name", "N_Por_Confirmar"], " en el libro · control I2"]],
  // B47 ="Este libro "&Version&" ("&TEXT(Fecha_Analisis,"dd-mmm-yyyy")&")"
  B47: ["tpl", ["Este libro ", ["name", "Version"], " (", ["call", "TEXT", [["name", "Fecha_Analisis"], ["str", "dd-mmm-yyyy"]]], ")"]],
  // C47 ="Bottom-up "&TEXT(CAPEX_Base_f1/(Potencia_DC*1000),"0.00")&" $/Wp sin IVA a "&TEXT(Potencia_DC/1000,"0.0")&" MWp (Base y Custom); × "
  //      &TEXT(INDEX(Esc_Factor_CAPEX,2),"0.00")&" en el Conservador; "&TEXT(INDEX(Esc_CAPEX_Fijo_Wp,4),"0.00")&" $/Wp fijo en el Favorable; escala por drivers Wp/Wac/fijo"
  C47: [
    "tpl",
    [
      "Bottom-up ",
      ["call", "TEXT", [["bin", "/", ["name", "CAPEX_Base_f1"], ["bin", "*", ["name", "Potencia_DC"], ["num", 1000]]], ["str", "0.00"]]],
      " $/Wp sin IVA a ",
      ["call", "TEXT", [["bin", "/", ["name", "Potencia_DC"], ["num", 1000]], ["str", "0.0"]]],
      " MWp (Base y Custom); × ",
      ["call", "TEXT", [["call", "INDEX", [["name", "Esc_Factor_CAPEX"], ["num", 2]]], ["str", "0.00"]]],
      " en el Conservador; ",
      ["call", "TEXT", [["call", "INDEX", [["name", "Esc_CAPEX_Fijo_Wp"], ["num", 4]]], ["str", "0.00"]]],
      " $/Wp fijo en el Favorable; escala por drivers Wp/Wac/fijo",
    ],
  ],
  // D47 =TEXT(OPEX_Anio1/1000,"#,##0")&" k (fee O&M "&TEXT(Fee_OM_kWp*Potencia_DC/1000,"0")&" k + seguros "&TEXT(Seguro_kWp*Potencia_DC/1000,"0.0")
  //      &" k + arriendo/predial + tributos "&TEXT(Tributos_Locales/1000,"0")&" k)"
  D47: [
    "tpl",
    [
      ["call", "TEXT", [["bin", "/", ["name", "OPEX_Anio1"], ["num", 1000]], ["str", "#,##0"]]],
      " k (fee O&M ",
      ["call", "TEXT", [["bin", "/", ["bin", "*", ["name", "Fee_OM_kWp"], ["name", "Potencia_DC"]], ["num", 1000]], ["str", "0"]]],
      " k + seguros ",
      ["call", "TEXT", [["bin", "/", ["bin", "*", ["name", "Seguro_kWp"], ["name", "Potencia_DC"]], ["num", 1000]], ["str", "0.0"]]],
      " k + arriendo/predial + tributos ",
      ["call", "TEXT", [["bin", "/", ["name", "Tributos_Locales"], ["num", 1000]], ["str", "0"]]],
      " k)",
    ],
  ],
};

/**
 * Columnas E («Fiscal») y F («Resultado reportado») de la tabla de §C (12_Fuentes!E43:F47): texto estático del libro que
 * `book.fuentes.cells` no incluye (sólo trae B–D). Se copian tal cual de la hoja.
 */
const SECCION_C_EF: Record<number, [string, string]> = {
  43: ["Fiscal", "Resultado reportado"],
  44: ["IR 25 %; doble depreciación sin tope; sin participación", "TIR 11,3 % · VAN +405 k · payback 7,5"],
  45: ["ídem", "TIR 9,6 % · VAN −131 k · payback 8,3"],
  46: ["no muestra TIR/VAN", "LCOE ≈ 85 vs 111 $/MWh · payback ≈ 6,2"],
  47: [
    "IR 25 % + participación 15 %; deducción adicional topada al 5 % de ingresos; IVA recuperable; ISD/arancel explícitos; peaje 2029 parametrizado; IDC sobre ambos tramos",
    "Ver 00_Portada (Custom con la tira C · B · F) y 10 §A (los cuatro casos)",
  ],
};

const stripBullet = (s: string) => s.replace(/^•\s*/, "");
const text = (v: Value | undefined): string => (v === null || v === undefined ? "" : Array.isArray(v) ? "" : String(v));

interface Grupo { title: string; head: CellRow; items: CellRow[] }

export function Fuentes({ onNavigate }: Props) {
  const m = useModel();
  const f = m.book.fuentes;

  // celdas agrupadas por cabecera de sección (filas cuyo B es una de las cinco cabeceras)
  const grupos = useMemo<Grupo[]>(() => {
    const out: Grupo[] = [];
    for (const c of [...f.cells].sort((a, b) => a.row - b.row)) {
      const b = c.v.B;
      if (typeof b === "string" && f.secciones.includes(b)) out.push({ title: b, head: c, items: [] });
      else out[out.length - 1]?.items.push(c);
    }
    return out;
  }, [f]);

  /** Texto de una celda: fórmula del libro evaluada en vivo si la hay; si no, el valor tal cual. */
  const cell = (c: CellRow, col: string): ReactNode => {
    const live = c.f?.[col] ? LIVE_CELLS[`${col}${c.row}`] : undefined;
    if (live) return <Live text={live} />;
    if (c.f?.[col]) return <span title={c.f[col]}>{text(c.v[col])}</span>;
    return text(c.v[col]);
  };

  const bullets = (g: Grupo | undefined) =>
    g ? (
      <ul className="flex flex-col divide-y divide-hairline">
        {g.items
          .filter((c) => text(c.v.B) !== "" || c.f?.B)
          .map((c) => (
            <li key={c.row} className="max-w-[110ch] py-1.5 font-serif text-[13px] leading-[1.5] text-ink-2">
              {c.f?.B ? cell(c, "B") : stripBullet(text(c.v.B))}
              {(text(c.v.C) !== "" || c.f?.C) && <span className="text-ink-3"> · {cell(c, "C")}</span>}
              {(text(c.v.D) !== "" || c.f?.D) && <span className="text-ink-3"> · {cell(c, "D")}</span>}
            </li>
          ))}
      </ul>
    ) : null;

  const seccion = (k: number): Grupo | undefined => grupos[k];
  const guideOf = (g: Grupo | undefined): ReactNode => (g && (text(g.head.v.C) !== "" || g.head.f?.C) ? cell(g.head, "C") : undefined);

  // §C · tabla de conciliación: primera fila con C = cabecera; resto con C = filas; sólo B = notas
  const secC = seccion(2);
  const tablaC = secC ? secC.items.filter((c) => text(c.v.C) !== "" || c.f?.C) : [];
  const notasC = secC ? secC.items.filter((c) => !(text(c.v.C) !== "" || c.f?.C) && text(c.v.B) !== "") : [];
  const headC = tablaC[0];
  const bodyC = tablaC.slice(1);
  const colsC: Column<CellRow>[] = headC
    ? [
        { key: "B", label: text(headC.v.B), width: "18%", render: (c) => <span className="text-ink">{cell(c, "B")}</span> },
        { key: "C", label: text(headC.v.C), width: "22%", render: (c) => <span className="text-ink-2">{cell(c, "C")}</span> },
        { key: "D", label: text(headC.v.D), width: "18%", render: (c) => <span className="text-ink-2">{cell(c, "D")}</span> },
        { key: "E", label: SECCION_C_EF[headC.row]?.[0] ?? "", width: "24%", render: (c) => <span className="text-ink-2">{SECCION_C_EF[c.row]?.[0] ?? ""}</span> },
        { key: "F", label: SECCION_C_EF[headC.row]?.[1] ?? "", render: (c) => <span className="text-ink-2">{SECCION_C_EF[c.row]?.[1] ?? ""}</span> },
      ]
    : [];

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="Fuentes y calidad" sheet="12_Fuentes" />

      {/* A · supuestos por confirmar */}
      <Section id="A" title={seccion(0)?.title ?? f.secciones[0]} guide={guideOf(seccion(0))}>
        <ul className="flex flex-col divide-y divide-hairline">
          {m.book.inputs.confirm_list.map((t, k) => {
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
          Los valores marcados se editan en{" "}
          <button type="button" className="text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid" onClick={() => onNavigate("supuestos")}>Supuestos</button>; el control I2 de{" "}
          <button type="button" className="text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid" onClick={() => onNavigate("controles")}>Controles</button> vigila que la lista esté al día.
        </Note>
      </Section>

      {/* B · simplificaciones declaradas */}
      <Section id="B" title={seccion(1)?.title ?? f.secciones[1]} guide={guideOf(seccion(1))}>
        {bullets(seccion(1))}
      </Section>

      {/* C · conciliación con los libros previos */}
      <Section id="C" title={secC?.title ?? f.secciones[2]} guide={guideOf(secC)}>
        {headC && <DataTable<CellRow> columns={colsC} rows={bodyC} rowKey={(c) => String(c.row)} emphasize={(c) => !!c.f?.B} />}
        {notasC.map((c) => (
          <Note key={c.row}>{cell(c, "B")}</Note>
        ))}
      </Section>

      {/* D · fuentes con enlace */}
      <Section id="D" title={seccion(3)?.title ?? f.secciones[3]} guide={guideOf(seccion(3)) ?? `${f.rows.length} fuentes · ${f.rows.filter((r) => r.url).length} con enlace`}>
        <ol className="flex flex-col divide-y divide-hairline">
          {f.rows.map((r, k) => (
            <li key={k} className="grid grid-cols-[28px_minmax(0,1fr)] items-start gap-x-2 py-2">
              <span className="pt-0.5 font-mono text-[10.5px] text-ink-3">{k + 1}</span>
              <div className="flex flex-col gap-0.5">
                <span className="max-w-[110ch] font-serif text-[13px] leading-[1.5] text-ink-2">
                  {stripBullet(r.texto)}
                  {r.url && (
                    <>
                      {" "}
                      <a href={r.url} target="_blank" rel="noreferrer" className="whitespace-nowrap font-sans text-[12px] text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid">
                        abrir ↗
                      </a>
                    </>
                  )}
                </span>
                {r.url && (
                  <a href={r.url} target="_blank" rel="noreferrer" className="break-all font-mono text-[10.5px] text-ink-3 hover:text-accent">
                    {r.url}
                  </a>
                )}
              </div>
            </li>
          ))}
        </ol>
      </Section>

      {/* E · convenciones e historial */}
      <Section id="E" title={seccion(4)?.title ?? f.secciones[4]} guide={guideOf(seccion(4))}>
        {bullets(seccion(4))}
      </Section>
    </div>
  );
}
