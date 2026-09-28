from pathlib import Path
import json
from kicad_common import parse,ser,child,children,val
R=Path(__file__).resolve().parents[1]/'integrated-power';path=R/'AQI_IP5310_Power.kicad_pcb';tree=parse(path.read_text())
def ref(f):return next((val(x[2]) for x in children(f,'property') if val(x[1])=='Reference'),'')
d=json.loads((R/'review/edge-pad-drc.json').read_text());ids={i['uuid'] for v in d['violations'] if v['type']=='shorting_items' for i in v['items'] if i['description'].startswith('Track')}
tree[:]=[a for a in tree if not(isinstance(a,list) and ((a[0]=='footprint' and ref(a) in ['TP9','TP10','TP11','TP12','TP13','TP14']) or (a[0]=='zone' and child(a,'keepout') is None) or (a[0]=='segment' and val(child(a,'uuid')[1]) in ids)))]
path.write_text(ser(tree)+'\n');print('Conflicting track removed:',len(ids))
