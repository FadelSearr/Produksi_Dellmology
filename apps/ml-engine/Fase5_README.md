Fase 5 — CNN Pattern Recognition (dev scaffold)

This folder contains a lightweight Keras scaffold for local development.

Quick start (dev):

- Option A (no TF): use the numpy fallback model (no extra deps).
- Option B (with TF): create a virtualenv and install TensorFlow:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install tensorflow
python inference_server.py
```

Endpoints:
- `/health` — health check
- `/infer?symbol=SYMBOL` — returns dummy predictions (uses keras_model if TF installed)

Notes:
- `keras_model.py` contains a tiny `SimpleCNN` that uses TF when available and
  falls back to uniform predictions otherwise.
- Replace the scaffold with a real trained model as you progress.
