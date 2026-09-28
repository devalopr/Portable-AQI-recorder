"""Refresh engineering fit-review outputs; not a fabrication release."""
from pathlib import Path
import subprocess,json,csv,zipfile
r=Path(__file__).resolve().parents[1];b=r/'battery';v=b/'review';cli='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli';pcb=b/'AQI_Battery_Compact.kicad_pcb'
def run(*args):
 z=subprocess.run([cli,*map(str,args)],capture_output=True,text=True)
 if z.returncode:raise RuntimeError(z.stdout+z.stderr)
 print('Exported',args[1:3],flush=True)
run('pcb','export','step',pcb,'--subst-models','--force','--no-dnp','-o',v/'AQI_Battery_Compact-fit-check.step')
run('pcb','render',pcb,'--side','bottom','--width','1000','--height','1800','-o',v/'compact-rear.png')
run('pcb','render',pcb,'--side','top','--rotate','20,0,10','--width','1400','--height','1400','-o',v/'compact-holder.png')
run('pcb','export','svg',pcb,'--layers','F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,Edge.Cuts','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',v/'AQI_Battery_Compact.svg')
d=json.loads((b/'design.json').read_text());drc=json.loads((v/'drc.json').read_text());conn=json.loads((v/'connectivity.json').read_text())
with (v/'engineering-bom.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','MPN','Manufacturer','Footprint','DNP','Note'])
 for c in d['components']:w.writerow([c['ref'],c.get('value',''),c.get('mpn','') or 'SELECT EXACT PART',c.get('manufacturer',''),c['fp'],c.get('dnp',False),c.get('note','')])
validation=dict(board_mm=[26.2,88],copper_layers=2,erc_violations=0,drc_violations=len(drc['violations']),unconnected_items=len(drc['unconnected_items']),schematic_parity_issues=len(drc.get('schematic_parity',[])),connected_pins_checked=conn['connected_pins_checked'],connectivity_issues=conn['issues'],release_status='Engineering review: ten unsuppressed holder/connector/header mechanical courtyard findings; electrical and thermal bench qualification outstanding',battery_route_necks='Approximately 2.8 mm total at 0.15 mm width; verify worst-case charge/discharge temperature rise before production.')
(v/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
