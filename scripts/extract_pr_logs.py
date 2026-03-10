import tarfile
from pathlib import Path
p = Path('pr-logs-20260310-041449.tar.gz')
outdir = Path('pr-logs-extracted-20260310-041449')
if not p.exists():
    print('MISSING', p)
else:
    outdir.mkdir(exist_ok=True)
    with tarfile.open(p, 'r:gz') as t:
        t.extractall(path=outdir)
    print('EXTRACTED to', outdir)
