import tarfile
from pathlib import Path
p = Path('pr-logs-20260310-041449.tar.gz')
out = Path('.pr_logs_listing.txt')
if not p.exists():
    out.write_text('MISSING: ' + str(p))
else:
    with tarfile.open(p, 'r:gz') as t:
        with out.open('w', encoding='utf-8') as f:
            for m in t.getmembers():
                f.write(m.name + '\n')
print('WROTE', out)
