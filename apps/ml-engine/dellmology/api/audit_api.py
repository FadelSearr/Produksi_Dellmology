from fastapi import APIRouter, Request, HTTPException
from typing import List
import logging
from sqlalchemy import text

from dellmology.utils.db_utils import get_db_connection, init_db

# Config may be available as local `config` module or via dellmology.utils.config
try:
    from config import Config
except Exception:
    try:
        from dellmology.utils.config import Config
    except Exception:
        # fallback placeholder when running in test environments without full config
        class _FallbackConfig:
            ADMIN_TOKEN = None

        Config = _FallbackConfig()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _check_admin(request: Request):
    token = request.headers.get('x-admin-token')
    if not token or token != Config.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/audit")
async def list_audit(request: Request, limit: int = 100):
    """List recent audit entries from `ml_audit_log`.

    Protected by `x-admin-token` header.
    """
    _check_admin(request)
    try:
        init_db()
    except Exception:
        # init_db may raise if DB is not available; return empty list gracefully
        logger.warning('Database not initialized, returning empty audit list')
        return {"entries": []}

    try:
        with get_db_connection() as conn:
            q = text("SELECT id, table_name, operation, changed_by, changed_at, payload FROM public.ml_audit_log ORDER BY changed_at DESC LIMIT :limit")
            res = conn.execute(q, {"limit": int(limit)})
            rows = res.fetchall()
            entries = [dict(r._mapping) for r in rows]
        return {"entries": entries}
    except Exception as e:
        logger.exception('Failed to fetch audit logs')
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/clear")
async def clear_audit(request: Request, older_than_days: int = 365):
    """Delete audit entries older than `older_than_days`.

    Protected by `x-admin-token` header.
    """
    _check_admin(request)
    try:
        init_db()
    except Exception:
        logger.warning('Database not initialized, nothing to clear')
        return {"deleted": 0}

    try:
        with get_db_connection() as conn:
            q = text("DELETE FROM public.ml_audit_log WHERE changed_at < now() - (:days || ' days')::interval RETURNING id")
            res = conn.execute(q, {"days": int(older_than_days)})
            deleted = len(res.fetchall())
        return {"deleted": deleted}
    except Exception as e:
        logger.exception('Failed to clear audit logs')
        raise HTTPException(status_code=500, detail=str(e))
