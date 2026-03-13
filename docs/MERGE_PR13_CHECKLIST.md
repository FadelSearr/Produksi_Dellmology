# Merge checklist for PR #13

Follow these steps before merging `feat/streamer-persistence-hardening-tests-clean` (PR #13).

1. CI green:
   - Trigger main CI (`.github/workflows/ci.yml`) and ensure `tests` job passes.
   - Confirm `per-file-tests.yml` artifacts exist and were inspected.

2. Review changes:
   - Confirm `apps/ml-engine` changes (LLM preload, admin endpoints) are correct.
   - Confirm `apps/web` Watchlist changes are minimal and tested.

3. Cleanup:
   - Ensure `.scripts/archive_debug` contains debug files and `.scripts/` no longer has temporary logs.
   - Confirm `.gitignore` contains large caches and model paths.

4. Documentation:
   - `docs/GGUF_PRELOAD_RUNBOOK.md` and `docs/LLM_DEPLOYMENT.md` present and accurate.

5. Final merge:
   - Squash-merge or rebase-merge depending on repo policy.
   - After merge, monitor CI on `main` for at least one successful run.
