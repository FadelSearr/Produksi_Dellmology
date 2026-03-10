"""
CI Monitor - download GitHub Actions run logs for a branch

Usage:
  export GITHUB_TOKEN=ghp_...  # or set in Windows: $env:GITHUB_TOKEN
  python scripts/ci_monitor.py --repo owner/repo --branch feat/streamer-persistence-hardening-tests --outdir run-logs

This script lists recent workflow runs for the provided branch and downloads
logs (zip) for any non-successful runs. It extracts the zip into the output
folder using the run id.

NOTE: Requires `requests`.
"""
import argparse
import os
import sys
import requests
import zipfile
import io
from datetime import datetime

API_BASE = "https://api.github.com"


def get_runs(repo, branch, token, per_page=50):
    url = f"{API_BASE}/repos/{repo}/actions/runs"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    params = {"branch": branch, "per_page": per_page}
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json().get("workflow_runs", [])


def download_logs(repo, run_id, token, outdir):
    url = f"{API_BASE}/repos/{repo}/actions/runs/{run_id}/logs"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    r = requests.get(url, headers=headers, stream=True)
    if r.status_code != 200:
        print(f"Failed to download logs for run {run_id}: HTTP {r.status_code}")
        return False
    z = zipfile.ZipFile(io.BytesIO(r.content))
    dest = os.path.join(outdir, f"run-{run_id}")
    os.makedirs(dest, exist_ok=True)
    z.extractall(dest)
    print(f"Extracted logs for run {run_id} -> {dest}")
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True, help="owner/repo")
    p.add_argument("--branch", required=True)
    p.add_argument("--outdir", default="run-logs")
    p.add_argument("--only-failed", action="store_true", help="Only download non-success runs")
    args = p.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is required")
        sys.exit(2)

    runs = get_runs(args.repo, args.branch, token)
    print(f"Found {len(runs)} runs for {args.repo}@{args.branch}")
    os.makedirs(args.outdir, exist_ok=True)
    for r in runs:
        run_id = r.get("id")
        status = r.get("status")
        conclusion = r.get("conclusion")
        created = r.get("created_at")
        print(f"Run {run_id}: status={status} conclusion={conclusion} created={created}")
        if args.only_failed and conclusion == "success":
            continue
        # Download logs for recent runs (limit to last 30 days)
        try:
            created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
        except Exception:
            created_dt = None
        if created_dt:
            age_days = (datetime.utcnow().replace(tzinfo=None) - created_dt.replace(tzinfo=None)).days
            if age_days > 30:
                continue
        try:
            download_logs(args.repo, run_id, token, args.outdir)
        except Exception as e:
            print(f"Failed to download/extract logs for run {run_id}: {e}")


if __name__ == '__main__':
    main()
