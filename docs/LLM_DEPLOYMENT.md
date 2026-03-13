# LLM Deployment Strategy — Recommendation

Summary
- Default: use remote LLM providers (OpenAI/Gemini) in production for reliability and lower operational cost.
- Local GGUF preload: supported for developer/experimental environments and for self-hosted deployments where data locality or offline operation is required.

When to use remote provider
- Production environments needing high availability, autoscaling, and managed updates.
- Teams that prefer SLA-backed inference and do not want to manage native bindings or large-model RAM requirements.

When to use local GGUF preload
- Development, experimentation, or air-gapped deployments.
- Use cases with strict data residency or latency requirements where hosting a model locally is justified.

Operational tradeoffs
- Remote provider: lower ops burden, predictable costs, but network dependency and potential data egress concerns.
- Local preload: greater ops complexity (native bindings, memory, swap, monitoring), hardware cost, and upgrade effort.

Recommended configuration for this repo
- Keep `LLM_PROVIDER` configurable via env. Default to `openai` or `mock` in CI.
- Keep `LLM_PRELOAD_ON_STARTUP` disabled by default; require an admin-triggered preload via the existing admin endpoint.
- Document steps to verify preload in `docs/GGUF_PRELOAD_RUNBOOK.md` (already added).
- Use deterministic fallback responses in tests to avoid flakiness when the local provider is unavailable.

Next steps
- Decide whether to enable local preload on any staging hosts (requires provisioning with >=8GB RAM and `llama-cpp` installed).
- If enabling local in staging, add monitoring (health, memory, and crash alerts) around `llm_backend` and admin endpoints.
