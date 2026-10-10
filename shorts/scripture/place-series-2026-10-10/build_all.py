from pathlib import Path
import subprocess,json,sys
r=Path(__file__).parent
for e in json.loads((r/'episodes.json').read_text(encoding='utf-8')):
 print('START '+e['slug'],flush=True)
 subprocess.run([sys.executable,'-X','utf8',str(r/e['slug']/'build.py')],check=True)
