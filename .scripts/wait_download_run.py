#!/usr/bin/env python3
"""Wait for a GitHub Actions run to complete and download its artifacts.

Usage: python .scripts/wait_download_run.py <run_id> [--repo owner/repo]
"""
import sys
import time
import subprocess
import os

def gh(cmd_args):
    p = subprocess.run(['gh'] + cmd_args, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

def run_status(run_id, repo):
    code, out, err = gh(['run', 'view', str(run_id), '--repo', repo, '--json', 'status,conclusion'])
    if code != 0:
        return None
    try:
        import json
        j = json.loads(out)
        return j.get('status'), j.get('conclusion')
    except Exception:
        return None

def download(run_id, repo, dest):
    os.makedirs(dest, exist_ok=True)
    code, out, err = gh(['run', 'download', str(run_id), '--repo', repo, '--dir', dest])
    return code == 0, out + err

def main():
    if len(sys.argv) < 2:
        print('usage: wait_download_run.py <run_id> [repo]')
        sys.exit(2)
    run_id = sys.argv[1]
    repo = sys.argv[2] if len(sys.argv) > 2 else 'FadelSearr/Produksi_Dellmology'
    dest = os.path.join('apps', 'ml-engine', 'test_logs', f'run_{run_id}')

    print('Polling run', run_id, 'on', repo)
    while True:
        st = run_status(run_id, repo)
        if st is None:
            print('Failed to query run status; retrying in 30s')
            time.sleep(30)
            continue
        status, concl = st
        print('Status:', status, 'Conclusion:', concl)
        if status == 'completed':
            ok, out = download(run_id, repo, dest)
            if ok:
                print('Downloaded artifacts to', dest)
            else:
                print('Download failed:', out)
            break
        time.sleep(30)

if __name__ == '__main__':
    main()
