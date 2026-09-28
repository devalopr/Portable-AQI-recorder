from pathlib import Path
import json
from kicad_common import parse,ser,child,val
r=Path(__file__).resolve().parents[1]/'battery';path=r/'AQI_Battery_Compact.kicad_pcb';d=json.loads((r/'review/drc.json').read_text());ids={i['uuid'] for v in d['violations'] if v['type'] in ['track_dangling','via_dangling'] for i in v['items']};raw=parse(path.read_text());raw[:]=[x for x in raw if not(isinstance(x,list) and (x[0]=='zone' or (x[0] in ['segment','via'] and val(child(x,'uuid')[1]) in ids)))];path.write_text(ser(raw));print('removed',len(ids),'unused ends/vias; recheck DRC')
