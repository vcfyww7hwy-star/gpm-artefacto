import { hrefForView } from "@/lib/hash";
import { NAV_GROUPS, type ViewId } from "@/lib/views";
import { cn } from "@/lib/utils";

interface Props {
  view: ViewId;
  onNavigate: (view: ViewId) => void;
  className?: string;
}

/**
 * Navegación izquierda agrupada. Enlaces reales (`href="#v=…"`) para que
 * funcionen teclado, clic medio y copiar-enlace; el estado se lee del hash.
 */
export function SideNav({ view, onNavigate, className }: Props) {
  return (
    <nav aria-label="Vistas" className={cn("flex flex-col gap-4 px-2 py-3", className)}>
      {NAV_GROUPS.map((group) => (
        <div key={group.id}>
          <p className="px-2 pb-1 text-[11px] font-medium uppercase tracking-[0.08em] text-ink-3">
            {group.label}
          </p>
          <ul className="flex flex-col">
            {group.views.map((v) => {
              const active = v.id === view;
              return (
                <li key={v.id}>
                  <a
                    href={hrefForView(v.id)}
                    aria-current={active ? "page" : undefined}
                    onClick={(e) => {
                      e.preventDefault();
                      onNavigate(v.id);
                    }}
                    className={cn(
                      "relative flex h-7 items-center rounded-1 px-2 text-[13px] text-ink-2 transition-colors",
                      "hover:bg-surface-hover hover:text-ink focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                      active && "bg-surface-hover font-medium text-ink",
                      active &&
                        "before:absolute before:-left-2 before:top-1.5 before:h-4 before:w-0.5 before:rounded-full before:bg-accent",
                    )}
                  >
                    {v.label}
                  </a>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

/** Variante horizontal para anchos estrechos: se desplaza en su propio contenedor. */
export function NavStrip({ view, onNavigate, className }: Props) {
  return (
    <nav
      aria-label="Vistas"
      className={cn("flex items-center gap-1 overflow-x-auto px-3 py-1.5", className)}
    >
      {NAV_GROUPS.map((group, gi) => (
        <div key={group.id} className="flex items-center gap-1">
          {gi > 0 && <span aria-hidden className="mx-1 h-4 w-px bg-hairline" />}
          {group.views.map((v) => {
            const active = v.id === view;
            return (
              <a
                key={v.id}
                href={hrefForView(v.id)}
                aria-current={active ? "page" : undefined}
                onClick={(e) => {
                  e.preventDefault();
                  onNavigate(v.id);
                }}
                className={cn(
                  "flex h-6 shrink-0 items-center rounded-1 px-2 text-[12.5px] text-ink-2 hover:bg-surface-hover hover:text-ink",
                  active && "bg-surface-hover font-medium text-ink",
                )}
              >
                {v.label}
              </a>
            );
          })}
        </div>
      ))}
    </nav>
  );
}
