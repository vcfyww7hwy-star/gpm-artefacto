import { useMemo, useState } from "react";

import { DataTable, type Column } from "@/components/DataTable";
import { Frozen } from "@/components/Live";
import { Status, stripGlyph } from "@/components/Status";
import { Note, Section, ViewHeader } from "@/components/ViewHeader";
import { fmtDate, fmtNum } from "@/lib/format";
import type { CaseId, ViewId } from "@/lib/views";
import { cn } from "@/lib/utils";
import { statusOf } from "@/model/book";
import { ORACLE, useModel } from "@/model/store";

/**
 * Controles (hoja 13_Controles): estado global del libro (resumen y conteos congelados) y, por separado, la autocomprobación
 * viva del motor (motor TS ≡ oráculo del Excel). La tabla lista los 79 controles por grupo con el estado del libro a la fecha
 * de corte: el motor recalcula las salidas, no los controles.
 */
interface Props {
  caseId: CaseId;
  onNavigate: (v: ViewId) => void;
}

interface Control { group: string; id: string; desc: string; status: string; formula: string; prueba: string | null }

const FORMULA_CUT = 72;

export function Controles({ onNavigate }: Props) {
  const m = useModel();
  const ctl = m.book.controles;
  const frozen = m.book.frozen;
  const [soloAvisos, setSoloAvisos] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());
  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const rows = useMemo<Control[]>(() => (soloAvisos ? ctl.rows.filter((r) => statusOf(r.status) !== "ok") : ctl.rows), [ctl, soloAvisos]);
  const nAvisos = ctl.rows.filter((r) => statusOf(r.status) !== "ok").length;
  const nCtrl = frozen.N_Controles as number, nOk = frozen.N_Controles_OK as number, nFail = frozen.N_Controles_Fail as number;
  const estado = String(ctl.resumen.Estado ?? frozen.Estado_Controles ?? "");
  const sc = m.selfCheck;
  const scKind = sc.status === "ok" ? "ok" : sc.status === "warn" ? "warn" : "risk";
  const version = m.book.meta.version, corte = fmtDate(m.book.meta.fecha_analisis);

  const columns: Column<Control>[] = [
    { key: "id", label: "#", mono: true, nowrap: true, width: "44px", render: (r) => r.id },
    {
      key: "desc",
      label: "Qué prueba",
      width: "38%",
      render: (r) => (
        <span className="flex flex-col gap-0.5">
          <span className="text-ink">{r.desc}</span>
          {r.prueba && <span className="text-[11px] text-ink-3">{r.prueba}</span>}
        </span>
      ),
    },
    {
      key: "estado",
      label: (
        <span className="inline-flex items-center">
          Estado
          <Frozen what="Control" />
        </span>
      ),
      width: "22%",
      render: (r) => (
        <Status kind={statusOf(r.status)} className="text-[11.5px]">
          {stripGlyph(r.status)}
        </Status>
      ),
    },
    {
      key: "formula",
      label: "Fórmula del libro",
      render: (r) => {
        const open = expanded.has(r.id);
        const long = r.formula.length > FORMULA_CUT;
        return (
          <button
            type="button"
            onClick={() => long && toggle(r.id)}
            title={open ? "Contraer" : r.formula}
            aria-expanded={open}
            className={cn("block max-w-full text-left font-mono text-[10.5px] text-ink-3", open ? "whitespace-pre-wrap break-all" : "truncate", long && "cursor-pointer hover:text-ink-2")}
          >
            {open || !long ? r.formula : `${r.formula.slice(0, FORMULA_CUT)}…`}
          </button>
        );
      },
    },
  ];

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-8">
      <ViewHeader title="Controles" sheet="13_Controles">
        {estado && (
          <Status kind={statusOf(estado)}>
            {stripGlyph(estado)}
            <Frozen what="Control" />
          </Status>
        )}
        {nFail > 0 && (
          <Status kind="risk">
            {nFail} control{nFail > 1 ? "es" : ""} en ■<Frozen what="Conteo" />
          </Status>
        )}
        <Status kind={scKind} mono>
          Motor ≡ Excel {sc.compared - sc.failed}/{sc.compared} salidas · {ORACLE.cases.length} casos
        </Status>
        {m.dirty > 0 && (
          <Status kind="info">
            sandbox: {m.dirty} entrada{m.dirty > 1 ? "s" : ""} distinta{m.dirty > 1 ? "s" : ""} del libro ·{" "}
            <button type="button" className="underline decoration-dotted underline-offset-2 hover:text-ink" onClick={m.reset}>volver al libro</button>
          </Status>
        )}
      </ViewHeader>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* resumen del libro (filas 95–99 de 13) */}
        <Section title="Estado del libro" guide={`resumen de la hoja a la fecha de corte (${version}, ${corte})`}>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-4">
            {Object.entries(ctl.resumen).map(([k, v]) => {
              const isText = typeof v === "string";
              return (
                <div key={k} className={cn("flex min-w-0 flex-col gap-1 border-t border-hairline pt-2", isText && "col-span-2")}>
                  <dt className="text-[10.5px] font-medium uppercase leading-tight tracking-[0.06em] text-ink-3">{k}</dt>
                  <dd className={cn(isText ? "text-[13px]" : "text-[24px] font-semibold leading-none tracking-[-0.01em]", "text-ink")} style={{ fontVariantNumeric: "tabular-nums" }}>
                    {isText ? (
                      <Status kind={statusOf(v)}>
                        {stripGlyph(v)}
                        <Frozen what="Control" />
                      </Status>
                    ) : (
                      <>
                        {typeof v === "number" ? fmtNum(v, 0) : String(v ?? "—")}
                        <Frozen what="Conteo" />
                      </>
                    )}
                  </dd>
                </div>
              );
            })}
          </dl>
          <Note>
            Los estados de los {fmtNum(nCtrl, 0)} controles ({fmtNum(nOk, 0)} en ●) son los del libro {version} a la fecha de corte ({corte}); el artefacto no los recalcula.
            Si cambia entradas en{" "}
            <button type="button" className="text-accent underline decoration-dotted underline-offset-2 hover:decoration-solid" onClick={() => onNavigate("supuestos")}>Supuestos</button> o Mandos, los
            controles siguen reflejando el libro entregado.
          </Note>
        </Section>

        {/* autocomprobación viva del motor */}
        <Section title="Autocomprobación del motor" guide="en vivo: motor TypeScript frente al oráculo (salidas de los casos del libro)">
          <div className="flex flex-col gap-2 border-t border-hairline pt-2">
            <div className="text-[24px] font-semibold leading-none tracking-[-0.01em] text-ink" style={{ fontVariantNumeric: "tabular-nums" }}>
              {fmtNum(sc.compared - sc.failed, 0)}/{fmtNum(sc.compared, 0)}
            </div>
            <Status kind={scKind} mono>
              Motor ≡ Excel · {ORACLE.cases.length} casos · {sc.namesOk ? "orden de casos verificado" : "orden de casos distinto del esperado"}
            </Status>
            {sc.failed > 0 && (
              <ul className="flex flex-col gap-0.5 font-mono text-[11px] text-risk">
                {sc.worst.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            )}
          </div>
          <Note>
            El motor recalcula los {m.cases.length} casos con las entradas entregadas ({ORACLE.version}, {fmtDate(ORACLE.fecha_analisis)}) y compara cada salida con la del libro;
            la comprobación no depende de los cambios hechos en la sesión. Recalcula salidas, no controles: la tabla de abajo es la del libro.
          </Note>
        </Section>
      </div>

      {/* tabla de controles */}
      <Section
        title="Los controles del libro"
        guide="identidades, candados y rangos agrupados como en la hoja · clic en una fórmula larga para desplegarla"
        aside={
          <div role="radiogroup" className="inline-flex h-7 items-stretch rounded-1 border border-hairline bg-surface p-px">
            {[
              { v: false, label: `Todos (${fmtNum(ctl.rows.length, 0)})` },
              { v: true, label: `Con aviso (${fmtNum(nAvisos, 0)})` },
            ].map((o) => (
              <button
                key={String(o.v)}
                type="button"
                role="radio"
                aria-checked={soloAvisos === o.v}
                onClick={() => setSoloAvisos(o.v)}
                className={cn("rounded-[3px] px-2.5 text-[12px] text-ink-2 hover:text-ink", soloAvisos === o.v && "bg-accent-soft font-medium text-accent")}
              >
                {o.label}
              </button>
            ))}
          </div>
        }
      >
        <DataTable<Control>
          columns={columns}
          rows={rows}
          rowKey={(r) => r.id}
          size="sm"
          sectionBefore={(r, i) => (i === 0 || rows[i - 1].group !== r.group ? r.group : null)}
          footer={`Estados del libro ${version} (${corte}); fórmulas tal cual en la hoja 13_Controles, columna D.`}
        />
        {rows.length === 0 && <p className="text-[12px] text-ink-3">Ningún control con aviso: todos en ●.</p>}
      </Section>
    </div>
  );
}
