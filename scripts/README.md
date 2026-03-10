Run the auto-prompt hooks runner

1. Install dependencies (recommended in a venv):

```bash
python -m pip install -r scripts/requirements.txt
```

2. Run the runner (example):

```bash
python scripts/run_auto_prompts.py --config .github/auto-prompts.yml
```

Notes
- The script is intentionally minimal. To integrate with a real agent, implement a subclass of `AgentInterface` in `scripts/run_auto_prompts.py` and wire it to your agent SDK/CLI.
- If a hook indicates code changes or the config sets `requires_confirmation_for_commits: true`, the runner will create a file under `.github/auto-prompts-pending/` for manual review and commit.

Auto-commit support (dangerous — opt-in required)
- To allow the runner to automatically commit changes produced by hooks, set `allow_auto_commit: true` in `.github/auto-prompts.yml` and set the environment variable `AUTO_PROMPTS_ALLOW_COMMIT=true` in the environment where the runner runs (for example, the GitHub Actions workflow or the host running the agent).
- To also allow automatic push, set `AUTO_PROMPTS_ALLOW_PUSH=true` in the environment and set the hook option `auto_push: true`.
- Example hook config enabling auto-commit (use with caution):

```yaml
enabled: true
allow_auto_commit: true
hooks:
	- name: "roadmap-check"
		trigger: "on_completion"
		prompt: "Lanjutkan sesuai roadmap"
		run_once_per_invocation: true
		auto_commit: true
		auto_push: false
```

Security note: automatic commits/pushes can be unsafe. Require explicit repository-level approval before enabling in CI. We require both config opt-in and environment variable to reduce accidental commits.
