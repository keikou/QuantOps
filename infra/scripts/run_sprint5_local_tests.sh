#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)

pushd "$ROOT_DIR/apps/v12-api" >/dev/null
pytest -q tests/test_sprint5_runtime_api.py tests/test_sprint5c_api.py tests/test_sprint5d_api.py tests/test_sprint5_integrated_api.py
popd >/dev/null

pushd "$ROOT_DIR/apps/quantops-api" >/dev/null
pytest -q app/tests/test_sprint5c_quantops_api.py app/tests/test_sprint5d_quantops_api.py app/tests/test_sprint5_integrated_quantops_api.py
popd >/dev/null
