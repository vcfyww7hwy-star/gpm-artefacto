import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { useModel } from "@/model/store";

/**
 * Cabecera estándar de vista: título (h1) · introducción de la hoja Excel equivalente (celda B2 del libro, misma redacción)
 * · fila opcional de chips (parámetros, estados). `sheet` = nombre de la hoja en book.sheets para tomar la introducción.
 */
export function ViewHeader({ title, sheet, intro, children, className }: { title: string; sheet?: string; intro?: ReactNode; children?: ReactNode; className?: string }) {
  const m = useModel();
  const text = intro ?? (sheet ? m.book.sheets[sheet]?.intro : null);
  return (
    <header className={cn("flex flex-col gap-1", className)}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h1 className="text-[20px] font-semibold tracking-[-0.01em] text-ink">{title}</h1>
        {sheet && <span className="font-mono text-[10.5px] text-ink-3" title="Hoja equivalente del libro Excel">{sheet}</span>}
      </div>
      {text && <p className="max-w-[92ch] text-[12.5px] text-ink-2">{text}</p>}
      {children && <div className="mt-1 flex flex-wrap gap-1.5">{children}</div>}
    </header>
  );
}

/** Sección con título y guía (misma anatomía que en Resumen y Sensibilidad). */
export function Section({ id, title, guide, children, className, aside }: { id?: string; title: ReactNode; guide?: ReactNode; children: ReactNode; className?: string; aside?: ReactNode }) {
  return (
    <section id={id} className={cn("flex flex-col gap-3", className)}>
      <header className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
          <h2 className="text-[13.5px] font-semibold text-ink">{title}</h2>
          {guide && <p className="text-[12px] text-ink-3">{guide}</p>}
        </div>
        {aside}
      </header>
      {children}
    </section>
  );
}

/** Chip monoespaciado (parámetros, nombres). */
export function Chip({ children, title, className }: { children: ReactNode; title?: string; className?: string }) {
  return <span title={title} className={cn("inline-flex items-center rounded-1 border border-hairline bg-surface px-1.5 py-0.5 font-mono text-[11px] text-ink-2", className)}>{children}</span>;
}

/** Nota al pie / aclaración en serif (lectura). */
export function Note({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn("max-w-[92ch] font-serif text-[13px] leading-[1.45] text-ink-2", className)}>{children}</p>;
}
