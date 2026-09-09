import { useEffect } from "react";

import { useDb } from "@/lib/capabilities";
import { SCENARIOS_COLLECTION, type Scenario } from "@/model/scenarios";
import { useModel } from "@/model/store";

/**
 * Enlace profundo `#s=<id>`: al abrir la página con un escenario en el hash, se carga desde la base del artefacto
 * (si está disponible) y se aplica a los Mandos. Sin `db` (edición externa, vista previa) no hace nada.
 */
export function ScenarioDeepLink() {
  const m = useModel();
  useEffect(() => {
    const id = new URLSearchParams(window.location.hash.replace(/^#/, "")).get("s");
    if (!id) return;
    let alive = true;
    useDb().then(async (db) => {
      if (!db || !alive) return;
      try {
        const snap = await db.doc(`${SCENARIOS_COLLECTION}/${id}`).get();
        if (alive && snap.exists) m.loadScenario({ id, ...(snap.data() as Omit<Scenario, "id">) });
      } catch {
        /* sin escenario: se queda el libro */
      }
    });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return null;
}
