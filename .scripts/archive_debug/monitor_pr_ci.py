"""Monitor PR CI runs and download artifacts for completed workflows.

Requires `gh` CLI authenticated and available in PATH.
"""
import json
import subprocess
import sys
import os

REPO = 'FadelSearr/Produksi_Dellmology'
BRANCH = 'feat/streamer-persistence-hardening-tests-clean'
OUTDIR = os.path.abspath(os.path.join('apps', 'ml-engine', 'ci_artifacts'))

os.makedirs(OUTDIR, exist_ok=True)

def gh_run_list():
    cmd = [
        'gh', 'run', 'list',
        '--repo', REPO,
        '--branch', BRANCH,
        '--limit', '50',
        '--json', 'databaseId,name,conclusion,status,url'
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print('gh run list failed:', p.stderr.strip())
        return []
    try:
        return json.loads(p.stdout)
    except Exception as e:
        print('Failed to parse gh output:', e)
        return []

def download_artifacts(run_id):
    dest = os.path.join(OUTDIR, str(run_id))
    os.makedirs(dest, exist_ok=True)
    cmd = ['gh', 'run', 'download', str(run_id), '--repo', REPO, '--dir', dest]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr

def main():
    runs = gh_run_list()
    if not runs:
        print('No runs found or failed to list runs.')
        return

    print(f'Found {len(runs)} runs on branch {BRANCH}')
    for r in runs:
        rid = r.get('databaseId')
        name = r.get('name')
        concl = r.get('conclusion')
        status = r.get('status')
        url = r.get('url')
        print(f'- {rid}: {name} [{status}/{concl}] {url}')
        if status == 'completed':
            print('  -> attempting to download artifacts...')
            code, out = download_artifacts(rid)
            if code == 0:
                print(f'  -> artifacts downloaded to {os.path.join(OUTDIR, str(rid))}')
            else:
                print(f'  -> download failed: {out.strip()}')

if __name__ == "__main__":
    main()
