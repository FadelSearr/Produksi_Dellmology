import subprocess, time, json, os, sys

def poll_and_download(run_id:int, max_wait=600, interval=8):
    elapsed = 0
    print('Polling run', run_id)
    while True:
        p = subprocess.run(['gh','run','view',str(run_id),'--json','status'], capture_output=True, text=True)
        if p.returncode != 0:
            print('gh returned', p.returncode, 'stdout:', p.stdout, 'stderr:', p.stderr)
        out = p.stdout.strip()
        status = None
        try:
            obj = json.loads(out)
            status = obj.get('status')
        except Exception:
            if 'in_progress' in out:
                status = 'in_progress'
            elif 'completed' in out:
                status = 'completed'
        print(f'status={status} (elapsed={elapsed}s)')
        if status in ('completed','failure','cancelled','skipped'):
            break
        time.sleep(interval)
        elapsed += interval
        if elapsed >= max_wait:
            print('timeout waiting for run to complete')
            break

    print('Fetching any failed-step logs')
    subprocess.run(['gh','run','view',str(run_id),'--log-failed','--exit-status'])
    outdir = f'artifacts-ml-{run_id}'
    print('Downloading artifacts to', outdir)
    subprocess.run(['gh','run','download',str(run_id),'-D',outdir])
    if os.path.exists(outdir):
        print('\nDownloaded files:')
        for root,dirs,files in os.walk(outdir):
            for f in files:
                fp = os.path.join(root,f)
                print(fp, os.path.getsize(fp))
    else:
        print('No artifacts downloaded')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: .tmp_poll_and_download.py <run_id>')
        sys.exit(2)
    rid = int(sys.argv[1])
    poll_and_download(rid)
