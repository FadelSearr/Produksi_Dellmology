"""Apply SQL migrations from db/init in numeric order.

Usage: python run_migrations.py
Environment: set `DATABASE_URL` or rely on Config.DATABASE_URL
"""
import os
import sys
from pathlib import Path
from sqlalchemy import text, create_engine

REPO_ROOT = Path(__file__).resolve().parents[3]
ML_ENGINE_PATH = REPO_ROOT / 'apps' / 'ml-engine'
MIGRATIONS_DIR = REPO_ROOT / 'db' / 'init'

if __name__ == '__main__':
    # Prefer using DATABASE_URL env var to avoid importing the whole package
    db_url = os.getenv('DATABASE_URL') or 'postgresql://admin:password@localhost:5433/dellmology'
    print('Using DATABASE_URL:', db_url)
    try:
        engine = create_engine(db_url)
        # quick test connection
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
    except Exception as e:
        print('Database init failed:', e)
        sys.exit(3)

    # Detect whether TimescaleDB extension is available. Some migrations
    # target Timescale-specific features; when missing, warn and allow
    # the runner to skip or run best-effort.
    is_timescale = False
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'timescaledb'"))
            rows = list(res)
            is_timescale = len(rows) > 0
    except Exception:
        is_timescale = False
    print('TimescaleDB available:', is_timescale)

    # Detect Supabase presence via env vars. Some migrations may be Supabase-
    # specific (create policies, roles, etc.) and should only run when a
    # Supabase project is configured.
    is_supabase = bool(os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
    print('Supabase configured:', is_supabase)

    files = sorted(p for p in MIGRATIONS_DIR.glob('*.sql'))
    if not files:
        print('No migrations found in', MIGRATIONS_DIR)
        sys.exit(0)

    # Apply each migration. Files that create materialized views or require
    # non-transactional execution (Timescale continuous aggregates) are run
    # with DBAPI autocommit; others are executed inside a transaction.
    for f in files:
        print('Applying', f.name)
        sql = f.read_text(encoding='utf-8')
        try:
            upper = sql.upper()
            # If this is a Timescale-specific statement and Timescale is not present,
            # print a warning and attempt to skip to avoid hard failures.
            if (('WITH (TIMESCALEDB.CONTINUOUS)' in upper or 'ADD_CONTINUOUS_AGGREGATE_POLICY' in upper) and not is_timescale):
                print(f"Skipping Timescale-specific migration {f.name} because TimescaleDB is not available")
                continue
            # If this migration file is marked as Supabase-only (use marker
            # "-- SUPABASE-ONLY" at top of SQL file), skip when no Supabase
            # credentials are available.
            if '-- SUPABASE-ONLY' in sql and not is_supabase:
                print(f"Skipping Supabase-only migration {f.name} because SUPABASE_URL/SERVICE_ROLE_KEY not set")
                continue
            if 'CREATE MATERIALIZED VIEW' in upper or 'CREATE MATERIALIZED VIEW CONCURRENTLY' in upper:
                # Some Timescale/PG statements (CREATE MATERIALIZED VIEW WITH DATA)
                # cannot run inside a transaction block. Prefer using a direct
                # psycopg2 connection with autocommit enabled. Fall back to the
                # SQLAlchemy raw_connection approach if psycopg2 is unavailable.
                executed = False
                try:
                    import psycopg2
                    conninfo = db_url
                    # Execute statements one-by-one; for CREATE MATERIALIZED VIEW
                    # use a fresh autocommit connection per statement to avoid
                    # any surrounding transaction.
                    parts = [p.strip() for p in sql.split(';') if p.strip()]
                    for part in parts:
                        if part.upper().startswith('CREATE MATERIALIZED VIEW') or part.upper().startswith('CREATE MATERIALIZED VIEW CONCURRENTLY'):
                            # use a fresh connection and set a reasonable statement timeout
                            cconn = psycopg2.connect(conninfo)
                            try:
                                ccur = cconn.cursor()
                                cconn.autocommit = True
                                ccur.execute("SET statement_timeout = 300000")
                                ccur.execute(part)
                                ccur.close()
                            finally:
                                try:
                                    cconn.close()
                                except Exception:
                                    pass
                        else:
                            # use a shared connection for non-problematic statements
                            if 'conn2' not in locals():
                                conn2 = psycopg2.connect(conninfo)
                                conn2.autocommit = True
                                cur2 = conn2.cursor()
                                cur2.execute("SET statement_timeout = 300000")
                            cur2.execute(part)
                    if 'cur2' in locals():
                        cur2.close()
                    if 'conn2' in locals():
                        conn2.close()
                    executed = True
                except Exception:
                        # fallback to raw SQLAlchemy DBAPI connection
                        import traceback
                        print('psycopg2 execution failed, falling back:', traceback.format_exc())
                        try:
                            raw = engine.raw_connection()
                            if hasattr(raw, 'autocommit'):
                                raw.autocommit = True
                            cur = raw.cursor()
                            parts = [p.strip() for p in sql.split(';') if p.strip()]
                            for part in parts:
                                try:
                                    cur.execute(part)
                                except Exception:
                                    print('raw execute failed for part:', part[:120])
                                    raise
                            cur.close()
                            executed = True
                        except Exception:
                            print('raw connection fallback also failed:')
                            import traceback as _tb
                            print(_tb.format_exc())
                            executed = False
                        finally:
                            try:
                                raw.close()
                            except Exception:
                                pass

                if not executed:
                    raise RuntimeError('Failed to execute autocommit migration statements')
            else:
                with engine.begin() as conn:
                    conn.execute(text(sql))
        except Exception as e:
            print(f'Failed to apply {f.name}:', e)
            # continue applying others (best-effort)
    print('Migrations complete')
