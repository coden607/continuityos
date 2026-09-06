#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python -m pytest -q
python -m compileall -q packages/python services
python -m pip install -e . --no-build-isolation >/dev/null
npm --prefix apps/web-pwa run build
node --check apps/web-pwa/src/app.js
node --check apps/web-pwa/src/service-worker.js
python -m json.tool apps/web-pwa/package.json >/dev/null
python -m json.tool packs/nextlaw607/pack.json >/dev/null
git diff --check
continuity doctor >/dev/null
continuity config-check continuity.toml.example >/dev/null
continuity execute "release-smoke" --config continuity.toml.example >/dev/null

# Secret/runtime safety: tracked files may not include private runtime state or common env secret files.
if git ls-files | grep -Ev '(^|/)\.env\.example$' | grep -E '(^|/)(\.env($|\.)|\.continuity/|.*\.agekey$|.*\.pem$)' >/dev/null; then
  echo "secret/runtime state file is tracked" >&2
  exit 1
fi

echo "ContinuityOS release verification passed."
