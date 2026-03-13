# GGUF Preload Runbook (Linux)

Purpose: verify local GGUF model preload for `apps/ml-engine` on a Linux VM with sufficient RAM (>=8GB recommended).

Prerequisites:
- Linux machine with >=8GB free RAM (more for larger models).
- Git checkout of this repo.
- Python 3.10+ (3.11/3.14 recommended).
- `git`, `curl`, and `gh` (optional) installed.
- Native binding `llama_cpp` installed (see notes below).

Quick steps (preferred):

1. Create and activate a virtualenv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r apps/ml-engine/requirements.txt
pip install llama-cpp-python
```

2. Place your GGUF model on the VM, e.g. `/models/my-model.gguf`.

3. Start the ml-engine FastAPI app locally (example):

```bash
export ML_ENGINE_KEY=devkey
export ADMIN_TOKEN=admintoken
export LLM_PROVIDER=local
export LLM_MODEL=/models/my-model.gguf
export LLM_PRELOAD_ON_STARTUP=false
cd apps/ml-engine
uvicorn main:app --host 0.0.0.0 --port 8000
```

4. Trigger preload via admin HTTP endpoint (recommended):

```bash
curl -X POST "http://127.0.0.1:8000/admin/llm/preload" -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{"model_path": "/models/my-model.gguf"}'
```

5. Check status:

```bash
curl -s "http://127.0.0.1:8000/admin/llm/status" -H "Authorization: Bearer $ADMIN_TOKEN" | jq
```

Alternate: run preload directly (inside repo) to debug without starting the server:

```bash
python -c "from dellmology.intelligence import llm_backend; print(llm_backend.preload_local_model('/models/my-model.gguf'))"
```

Troubleshooting:
- If `llama_cpp` import fails, install the wheel matching your platform/GLIBC or build from source. See https://github.com/juncongmoo/llama-cpp-python for details.
- If instantiation fails with OOM or crash, increase VM RAM or use swap (performance will suffer).
- If model loads on disk but `preload_local_model` returns a sentinel (not fully preloaded), check for platform-specific native binding errors in the process stdout/stderr.

Notes:
- Running on Windows often fails due to native linking and memory limits. Use Linux for verification.
- Admin endpoints require `ADMIN_TOKEN` to be set and provided in the Authorization header.
