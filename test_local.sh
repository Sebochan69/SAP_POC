#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if python3 -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))' >/dev/null 2>&1; then
  PYTHON=(python3)
elif python -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))' >/dev/null 2>&1; then
  PYTHON=(python)
elif py -3.12 -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))' >/dev/null 2>&1; then
  PYTHON=(py -3.12)
else
  echo "Python 3.12 is required. Install it or make 'py -3.12' available in Git Bash." >&2
  exit 1
fi

"${PYTHON[@]}" verify.py
"${PYTHON[@]}" -m py_compile \
  app.py errors.py ollama_client.py integration_contract.py \
  mock_adapter.py mock_demo.py mock_sap_sandbox.py
"${PYTHON[@]}" mock_demo.py

echo "ALL LOCAL TESTS PASSED"
