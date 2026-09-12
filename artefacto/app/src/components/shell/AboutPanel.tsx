import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { EDITION_DATA, book } from "@/model/edition-data";
import { ORACLE, useModel } from "@/model/store";
import { describePatch, diffInputs, diffExtras } from "@/model/scenarios";
import { BASELINE_EXTRAS, BASELINE_INPUTS } from "@/model/store";

/**
 * A9/G4 (doc 25): panel «Acerca de esta versión». Todo lo que aquí se muestra son METADATOS del artefacto y de la extracción
 * del libro (book.meta, oráculo, edición, entradas modificadas) — textos de interfaz, no contenido del modelo.
 */
export const ARTEFACTO_VERSION = "v2 · ola 1 · r4 (11-sep-2026) · libro v3.1 r3";

/** Historial de publicaciones (se actualiza en cada promoción; G4). */
export const CHANGELOG: ReadonlyArray<{ version: string; fecha: string; nota: string }> = [
  { version: "v2 · ola 1 · r4 · libro v3.1 r3", fecha: "11-sep-2026", nota: "Libro v3.1 r3 (G-L2 aprobado): la barra «Escalación tarifa» del tornado pasa a Custom + 1 pp (antes coincidía con el Custom y medía 0); 00b explica la regla de la TIR del accionista (D-V2-9); el Resumen para el Directorio corrige su etiqueta (v3.1 · 08-sep-2026). Motor ≡ libro r3: 91.546/0." },
  { version: "F5 r2 · hotfix F1-01", fecha: "09-sep-2026", nota: "Resumen: el criterio de los candados 4 y 5 se evalúa en vivo (antes se mostraba la fórmula sin evaluar)." },
  { version: "v2 · ola 1 · r3", fecha: "11-sep-2026", nota: "Prueba en el visor real (A1): recuerda la última vista y caso; «Copiar enlace» copia la URL pública; «Acerca de» también desde ⌘K; reglas de escritura en escenarios verificadas." },
  { version: "v2 · ola 1 · r2", fecha: "09-sep-2026", nota: "TIR ≡ Excel (D-V2-9) · contraste AA en ambos temas · tamaños mínimos · límite de error por vista · panel «Acerca de» · indicador de desplazamiento en tablas · borrado lógico con papelera." },
  { version: "F5 r1", fecha: "08-sep-2026", nota: "Escenarios (db), exportar CSV/JSON, impresión, ⌘K, edición externa." },
];

interface Props { open: boolean; onOpenChange: (o: boolean) => void }

export function AboutPanel({ open, onOpenChange }: Props) {
  const m = useModel();
  const meta = (book as { meta?: Record<string, string> }).meta ?? {};
  const passed = m.selfCheck.compared - m.selfCheck.failed;
  const rows: Array<[string, string]> = [
    ["Edición", (EDITION_DATA as string) === "externo" ? "externa (SALELGI) — sin los internos de Exergy" : "interna (Exergy)"],
    ["Artefacto", ARTEFACTO_VERSION],
    ["Libro origen", `${meta.version ?? ORACLE.version} · fecha de análisis ${meta.fecha_analisis ?? ORACLE.fecha_analisis}`],
    ["Extracción", `${meta.extracted ?? "—"} · ${meta.generator ?? "build30"}`],
    ["SHA del cálculo (LibreOffice)", (meta.calc_sha256 ?? ORACLE.calc_sha256 ?? "").slice(0, 16) + "…"],
    ["Motor ≡ Excel", `${passed}/${m.selfCheck.compared} salidas de ${ORACLE.cases.length} casos coinciden con el libro (tolerancia 1e-9)`],
    ["Convención numérica", "es-EC: punto de miles y coma decimal (1.234,56 · 10,64 %). Excel en un Mac configurado en en-EC muestra 1,234.56 · 10.64% — mismos valores, distinta escritura."],
    ["TIR", "Newton desde la semilla del libro; si no converge o sale del dominio, raíz única en (−99 %, +1.000 %); varias raíces → «n/a» (igual que Excel; D-V2-9)."],
    ["Enlaces", "El visor de claude.ai abre el artefacto siempre en la última vista que usó en este navegador; los enlaces internos (#v= · #c= · #s= · #f=) funcionan dentro del artefacto. «Copiar enlace» copia la URL pública y describe la vista, el caso y el escenario."],
  ];
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] w-[min(96vw,720px)] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Acerca de esta versión</DialogTitle>
          <DialogDescription>Qué libro está viendo, con qué versión del artefacto y si se ha alejado de él.</DialogDescription>
        </DialogHeader>
        <dl className="grid grid-cols-[176px_minmax(0,1fr)] gap-x-4 gap-y-2 text-[12.5px]">
          {rows.map(([k, v]) => (
            <div key={k} className="contents">
              <dt className="text-ink-3">{k}</dt>
              <dd className="text-ink">{v}</dd>
            </div>
          ))}
          <dt className="text-ink-3">Entradas ≠ libro</dt>
          <dd className="text-ink">
            {m.dirty === 0 && m.dirtyExtras.length === 0 ? (
              "ninguna — está viendo exactamente el libro"
            ) : (
              <span>
                {m.dirty + m.dirtyExtras.length} modificada(s): {describePatch(diffInputs(m.inputs, BASELINE_INPUTS), diffExtras(m.extras, BASELINE_EXTRAS)).join(" · ")}
                <button type="button" onClick={() => { m.reset(); }} className="ml-2 rounded-1 border border-hairline px-1.5 py-0.5 text-[11.5px] hover:bg-surface-hover">
                  volver al libro
                </button>
              </span>
            )}
          </dd>
        </dl>
        <h3 className="mt-3 text-[11px] font-medium uppercase tracking-[0.06em] text-ink-3">Historial de versiones</h3>
        <ul className="divide-y divide-hairline text-[12px]">
          {CHANGELOG.map((c) => (
            <li key={c.version} className="grid grid-cols-[176px_minmax(0,1fr)] gap-x-4 py-1.5">
              <span className="text-ink-2">{c.fecha} · <span className="font-mono">{c.version}</span></span>
              <span className="text-ink">{c.nota}</span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[11px] text-ink-3">Los textos de este panel son de la interfaz del artefacto, no del libro.</p>
      </DialogContent>
    </Dialog>
  );
}
