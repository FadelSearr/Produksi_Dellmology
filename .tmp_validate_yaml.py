import sys
from pathlib import Path
p=Path('.github/workflows/pr-monitor.yml')
if not p.exists():
    print('MISSING_FILE')
    sys.exit(2)
text=p.read_text()
try:
    import yaml
except Exception as e:
    print('MISSING_PYYAML', e)
    sys.exit(3)
try:
    yaml.safe_load(text)
    print('YAML_PARSE_OK')
except Exception as e:
    print('YAML_PARSE_ERROR', e)
    sys.exit(1)
