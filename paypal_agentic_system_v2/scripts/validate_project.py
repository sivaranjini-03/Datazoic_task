import json, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
registry=json.loads((root/'data/tool_registry.json').read_text())
print('Registry tools:',registry['tool_count'])
assert registry['tool_count']==116
r=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=root)
raise SystemExit(r.returncode)
