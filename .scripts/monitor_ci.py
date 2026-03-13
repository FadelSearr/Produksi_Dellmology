import json
import os
import subprocess
from pathlib import Path

# Configuration
REPO = 'FadelSearr/Produksi_Dellmology'
BRANCH = 'feat/streamer-persistence-hardening-tests-clean'
OUT_DIR = Path('apps/ml-engine/test_logs')
SEEN_FILE = Path('.scripts/.seen_runs.json')

OUT_DIR.mkdir(parents=True, exist_ok=True)
SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)

def run_cmd(cmd):
    # Prefer passing a sequence of args (no shell) to avoid Windows quoting issues.
    if isinstance(cmd, (list, tuple)):
        proc = subprocess.run(cmd, capture_output=True, text=True)
    else:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr

def load_seen():
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()

def save_seen(s):
    SEEN_FILE.write_text(json.dumps(list(s)))

def list_runs():
    cmd = [
        'gh', 'run', 'list',
        '--repo', REPO,
        '--branch', BRANCH,
        '--limit', '50',
        '--json', 'databaseId,name,status,conclusion,url',
        '--jq', ".[] | {id:.databaseId, name:.name, status:.status, conclusion:.conclusion, url:.url}"
    ]
    code, out, err = run_cmd(cmd)
    if code != 0:
        print('gh run list failed', err)
        return []
    # Each line is a JSON object
    runs = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            runs.append(json.loads(line))
        except Exception:
            # skip
            pass
    return runs

def download_run(run_id):
    target = OUT_DIR / f'run_{run_id}'
    target.mkdir(parents=True, exist_ok=True)
    cmd = [
        'gh', 'run', 'download', str(run_id),
        '--repo', REPO,
        '--dir', str(target),
        '--quiet'
    ]
    code, out, err = run_cmd(cmd)
    if code == 0:
        print(f'Downloaded artifacts for run {run_id} -> {target}')
        return True
    else:
        print(f'No artifacts or failed to download for run {run_id}:', err.strip())
        return False

def main():
    seen = load_seen()
    runs = list_runs()
    new_seen = set(seen)
    for r in runs:
        rid = str(r.get('id'))
        name = r.get('name')
        concl = r.get('conclusion')
        if concl != 'success' and concl != 'failure':
            continue
        if rid in seen:
            continue
        print('Found run', rid, name, '->', concl)
        # attempt to download artifacts
        download_run(rid)
        new_seen.add(rid)
    save_seen(new_seen)

if __name__ == '__main__':
    main()
