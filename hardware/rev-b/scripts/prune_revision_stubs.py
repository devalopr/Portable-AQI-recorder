from pathlib import Path
import sys,json,subprocess,os
from kicad_common import parse,ser,child,val
R=Path(__file__).resolve().parents[1]/'integrated-power';path=R/'AQI_IP5310_Power.kicad_pcb';report=R/'review/routing-drc.json';cli='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
for turn in range(15):
 d=json.loads(report.read_text());ids={i['uuid'] for v in d['violations'] if v['type'] in ['track_dangling','via_dangling'] for i in v['items']}
 if not ids:break
 a=parse(path.read_text());a[:]=[x for x in a if not(isinstance(x,list) and x[0] in ['segment','via'] and val(child(x,'uuid')[1]) in ids)];path.write_text(ser(a))
 subprocess.run([cli,'pcb','drc','--format','json','-o',str(report),str(path)],env=dict(os.environ,FONTCONFIG_FILE='/tmp/aqi-fonts.conf'),stdout=subprocess.DEVNULL,check=True)
 print('pruned',turn,len(ids),flush=True)
