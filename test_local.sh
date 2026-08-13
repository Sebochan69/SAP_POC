#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHON=python3
command -v "$PYTHON" >/dev/null 2>&1 || PYTHON=python

"$PYTHON" verify.py
"$PYTHON" -m py_compile \
  app.py errors.py ollama_client.py integration_contract.py \
  mock_adapter.py mock_demo.py mock_sap_sandbox.py
"$PYTHON" mock_demo.py

echo "ALL LOCAL TESTS PASSED"
