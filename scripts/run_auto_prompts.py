#!/usr/bin/env python3
"""
Minimal runner for repository auto-prompt hooks.

Usage:
  python scripts/run_auto_prompts.py --config .github/auto-prompts.yml

This script is intentionally minimal and pluggable: implement an Agent subclass
to call your real agent/CLI/API. The default LocalAgent echoes prompts.
"""
import argparse
import os
import sys
import logging
import uuid
from datetime import datetime
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

LOG_FILE = Path('.github/auto-prompts.log')


class AgentResult:
    def __init__(self, finished: bool, output: str = "", would_commit: bool = False, changed_files=None):
        self.finished = finished
        self.output = output
        self.would_commit = would_commit
        self.changed_files = changed_files or []


class AgentInterface:
    def execute(self, prompt: str) -> AgentResult:
        """Override to call real agent/SDK/CLI. Return AgentResult."""
        raise NotImplementedError()


class LocalAgent(AgentInterface):
    def execute(self, prompt: str) -> AgentResult:
        # Simple echo agent for demonstration
        out = f"[LocalAgent] Executed prompt: {prompt}\n"
        # If prompt contains the token "COMMIT:" we simulate a change
        would_commit = "COMMIT:" in prompt
        changed = ["example.txt"] if would_commit else []
        return AgentResult(finished=True, output=out, would_commit=would_commit, changed_files=changed)


def load_config(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install scripts/requirements.txt or `pip install pyyaml`.")
    with path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def log_entry(text: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open('a', encoding='utf-8') as fh:
        fh.write(text + "\n")


def contains_secret_like_token(prompt: str) -> bool:
    # Basic heuristic to avoid accidentally running prompts that leak secrets
    secret_keywords = ['SECRET', 'TOKEN', 'KEY', 'PASSWORD', 'PWD', 'AWS_ACCESS', 'AWS_SECRET']
    up = prompt.upper()
    return any(k in up for k in secret_keywords)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='.github/auto-prompts.yml')
    parser.add_argument('--depth', type=int, default=0)
    parser.add_argument('--agent', choices=['local'], default='local')
    parser.add_argument('--run-id', default=None, help='Identifier for this invocation to enforce run_once_per_invocation')
    args = parser.parse_args(argv)

    cfg_path = Path(args.config)
    cfg = load_config(cfg_path)

    if not cfg.get('enabled'):
        print('Auto-prompts are disabled in config.')
        return 0

    max_depth = int(cfg.get('max_chain_depth', 2))
    if args.depth >= max_depth:
        print(f"Max chain depth reached ({args.depth} >= {max_depth}). Exiting.")
        return 0

    # run_id ensures run_once_per_invocation across recursive invocations
    run_id = args.run_id or uuid.uuid4().hex
    runs_root = Path('.github/auto-prompts-runs')
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    hooks = cfg.get('hooks', []) or []
    whitelist = set(cfg.get('whitelist', []) or [])
    blacklist = set(cfg.get('blacklist', []) or [])

    agent: AgentInterface = LocalAgent()

    for hook in hooks:
        if hook.get('trigger') != 'on_completion':
            continue
        name = hook.get('name')

        # whitelist / blacklist enforcement
        if whitelist and name not in whitelist:
            print(f"Skipping hook {name}: not in whitelist.")
            log_entry(f"HOOK:{name} SKIPPED_NOT_WHITELISTED")
            continue
        if name in blacklist:
            print(f"Skipping hook {name}: blacklisted.")
            log_entry(f"HOOK:{name} SKIPPED_BLACKLISTED")
            continue

        # enforce run_once_per_invocation
        if hook.get('run_once_per_invocation'):
            marker = run_dir / f"{name}.ran"
            if marker.exists():
                print(f"Skipping hook {name}: already run in this invocation ({run_id}).")
                log_entry(f"HOOK:{name} SKIPPED_ALREADY_RUN run_id={run_id}")
                continue

        prompt = hook.get('prompt')

        # simple secret check
        if contains_secret_like_token(prompt):
            print(f"Skipping hook {name}: prompt appears to contain secret-like tokens.")
            log_entry(f"HOOK:{name} SKIPPED_SECRET_CHECK")
            continue

        print(f"Running hook: {name}")
        log_entry(f"HOOK:{name} START {datetime.utcnow().isoformat()} run_id={run_id}")
        result = agent.execute(prompt)
        log_entry(f"HOOK:{name} OUTPUT:\n{result.output}")

        # record that this hook ran for this invocation
        if hook.get('run_once_per_invocation'):
            marker.write_text(datetime.utcnow().isoformat())

        if result.would_commit or hook.get('requires_confirmation_for_commits'):
            # Do not auto-commit. Save patch placeholder and log, with clear confirm instructions.
            pending_dir = Path('.github/auto-prompts-pending')
            pending_dir.mkdir(parents=True, exist_ok=True)
            pending_file = pending_dir / f"{name}.txt"
            with pending_file.open('w', encoding='utf-8') as pf:
                pf.write(f"Hook: {name}\nPrompt: {prompt}\n\nAgent output:\n{result.output}\n\nChanged files: {result.changed_files}\n\n" )
                pf.write("To apply these changes, review them and run: git add <files> && git commit -m \"auto-prompt: apply <hook>\"\n")
            log_entry(f"HOOK:{name} PENDING_CHANGE: {pending_file}")
            print(f"Hook {name} produced changes. Saved pending file: {pending_file}. Commit requires manual confirmation.")
        else:
            print(f"Hook {name} completed with no commit-worthy changes.")

    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
