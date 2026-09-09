#!/usr/bin/env bash
# release.sh — G2 (doc 25/26): cadena completa de release del artefacto interactivo.
#   verify (motor ≡ LibreOffice) → test:irr (≡ Excel, D-V2-9) → live.test → format.test → tsc → build:editions (+check:exclusion)
#   → smoke (Playwright, ambas ediciones) → SHA-256 → copia en publicados/<etiqueta>/ (G9) → fragmentos «Candidato» (G3).
# Uso: scripts/release.sh "<etiqueta de versión>"      (desde artefacto/app/; ENGINE_DIR opcional)
# La publicación en claude.ai se hace con la herramienta Artifact: primero los candidatos (out/candidato/*.fragment.html),
# después — con la palabra «promover» de Jorge — los oficiales (out/<edición>/fragment.html) con `url` + `label`.
set -euo pipefail
LABEL="${1:-sin-etiqueta}"
APP="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE="${ENGINE_DIR:-$APP/../engine}"
PUB="$APP/../publicados/$(date +%Y-%m-%d)_$(echo "$LABEL" | tr ' /·' '___' | tr -cd 'A-Za-z0-9_.-')"
log() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

log "1/8 motor ≡ LibreOffice (verify.ts)"
( cd "$ENGINE" && npx tsx test/verify.ts | tail -1 )
log "2/8 TIR ≡ Excel (irr_excel.test.ts) + invariante VAN(TIR)≈0"
( cd "$ENGINE" && npx tsx test/irr_excel.test.ts | tail -1 )
log "3/8 textos vivos (live.test) y formato es-EC (format.test)"
( cd "$APP" && npx tsx test/live.test.ts | tail -1 && npx tsx test/format.test.ts | tail -1 )
log "4/8 tipos (tsc -b)"
( cd "$APP" && npx tsc -b && echo "tsc OK" )
log "5/8 build de ediciones + check:exclusion"
( cd "$APP" && npm run build:editions 2>&1 | grep -E "✔|✖|OK|Error" | tail -6 )
log "6/8 smoke Playwright (interno y externo)"
for ed in interno externo; do
  if ! ( cd "$APP" && node scripts/smoke.mjs "$ed" > "/tmp/smoke_$ed.log" 2>&1 ); then echo "✖ smoke $ed"; grep -E "✖|fuga|desbordes|errores" "/tmp/smoke_$ed.log"; exit 1; fi
  printf '  ✔ smoke %s: %s comprobaciones\n' "$ed" "$(grep -c '✔' "/tmp/smoke_$ed.log")"
done
log "7/8 SHA-256 y copia en publicados/ (G9)"
mkdir -p "$PUB"
for ed in interno externo; do
  cp "$APP/out/$ed/fragment.html" "$PUB/$ed.fragment.html"
  cp "$APP/out/$ed/fragment.report.json" "$PUB/$ed.fragment.report.json"
done
( cd "$PUB" && sha256sum *.fragment.html > SHA256SUMS.txt && cat SHA256SUMS.txt )
printf '{"label": "%s", "date": "%s", "engine": "%s"}\n' "$LABEL" "$(date -u +%FT%TZ)" "$(cd "$ENGINE" && git -C "$ENGINE" rev-parse --short HEAD 2>/dev/null || echo n/a)" > "$PUB/release.json"
log "8/8 fragmentos «Candidato» (G3: idénticos salvo el <title>)"
mkdir -p "$APP/out/candidato"
python3 - "$APP" <<'EOF'
import sys, hashlib
app = sys.argv[1]
for ed, old, new in (("interno", "<title>Modelo FV Montecristi → GPM</title>", "<title>Candidato · Modelo FV Montecristi → GPM</title>"),
                     ("externo", "<title>Proyecto FV Montecristi → GPM</title>", "<title>Candidato · Proyecto FV Montecristi → GPM</title>")):
    s = open(f"{app}/out/{ed}/fragment.html", encoding="utf-8").read()
    assert s.count(old) == 1, (ed, s.count(old))
    c = s.replace(old, new, 1)
    open(f"{app}/out/candidato/{ed}.fragment.html", "w", encoding="utf-8").write(c)
    print(f"  {ed}: oficial {hashlib.sha256(s.encode()).hexdigest()[:8]} ({len(s.encode()):,} B) · candidato {hashlib.sha256(c.encode()).hexdigest()[:8]} · sólo <title>: {c.replace(new, old) == s}")
EOF
printf '\n\033[1mRelease «%s» lista.\033[0m Publicar candidatos: %s/out/candidato/{interno,externo}.fragment.html · copia: %s\n' "$LABEL" "$APP" "$PUB"
