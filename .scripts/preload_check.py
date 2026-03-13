"""Small helper to call the admin preload/status endpoints for local verification.

Usage: set `ADMIN_TOKEN` and run `python .scripts/preload_check.py preload /models/my-model.gguf`
"""
import os
import sys
import requests

BASE = os.environ.get('ML_ENGINE_URL', 'http://127.0.0.1:8000')
TOKEN = os.environ.get('ADMIN_TOKEN')

def headers():
    if not TOKEN:
        raise SystemExit('Set ADMIN_TOKEN env var')
    return {'Authorization': f'Bearer {TOKEN}'}

def preload(model_path):
    url = f"{BASE}/admin/llm/preload"
    r = requests.post(url, headers=headers(), json={'model_path': model_path})
    print(r.status_code, r.text)

def status():
    url = f"{BASE}/admin/llm/status"
    r = requests.get(url, headers=headers())
    print(r.status_code)
    print(r.text)

def main():
    if len(sys.argv) < 2:
        print('usage: preload|status [model_path]')
        return
    cmd = sys.argv[1]
    if cmd == 'preload':
        if len(sys.argv) < 3:
            print('need model_path')
            return
        preload(sys.argv[2])
    elif cmd == 'status':
        status()
    else:
        print('unknown cmd')

if __name__ == '__main__':
    main()
