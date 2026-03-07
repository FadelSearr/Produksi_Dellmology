"""Simple checkpoint manager for model retraining.

This stores checkpoint metadata on disk under `models/checkpoints/` and
provides helpers to list/load/save checkpoints. Designed for a lightweight
developer-run environment; replace with object store (S3) in production.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

ROOT = Path(__file__).parent.parent.parent
CHECKPOINT_DIR = ROOT / "models" / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def _checkpoint_path(name: str) -> Path:
    safe = name.replace(' ', '_')
    return CHECKPOINT_DIR / f"{safe}.json"


def save_checkpoint(model_name: str, metrics: Dict, metadata: Optional[Dict] = None) -> str:
    """Save a checkpoint metadata file and return its filename."""
    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    name = f"{model_name}_{ts}"
    payload = {
        'model_name': model_name,
        'name': name,
        'metrics': metrics or {},
        'metadata': metadata or {},
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    path = _checkpoint_path(name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    return name


def list_checkpoints() -> List[Dict]:
    files = sorted(CHECKPOINT_DIR.glob('*.json'), reverse=True)
    out = []
    for p in files:
        try:
            with open(p, 'r', encoding='utf-8') as f:
                out.append(json.load(f))
        except Exception:
            continue
    return out


def load_checkpoint(name: str) -> Optional[Dict]:
    path = _checkpoint_path(name)
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None
