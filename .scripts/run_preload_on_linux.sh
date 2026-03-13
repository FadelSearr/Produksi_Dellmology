#!/usr/bin/env bash
# Helper to run model preload on a Linux VM (run from repository root)
set -euo pipefail

MODEL_PATH=${1:-/models/my-model.gguf}

if [ ! -f "$MODEL_PATH" ]; then
  echo "Model not found: $MODEL_PATH" >&2
  exit 2
fi

echo "Activating virtualenv .venv (create if missing)"
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
else
  python -m venv .venv
  source .venv/bin/activate
  pip install -r apps/ml-engine/requirements.txt
  pip install llama-cpp-python
fi

echo "Running direct preload using python API"
python - <<PY
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path('.').absolute() / 'apps' / 'ml-engine'))
try:
    from dellmology.intelligence import llm_backend
except Exception as e:
    print('Import error:', e)
    raise

print('Calling preload_local_model...')
res = llm_backend.preload_local_model(model_path='$MODEL_PATH')
print('Result:', json.dumps(res, indent=2))
PY

echo "Done"
