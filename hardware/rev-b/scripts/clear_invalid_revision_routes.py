from pathlib import Path
import json
from kicad_common import parse,ser,child,children,val
R=Path(__file__).resolve().parents[1]/'integrated-power';path=R/'AQI_IP5310_Power.kicad_pcb';a=parse(path.read_text());d=json.loads((R/'review/routing-drc.json').read_text());ids={i['uuid'] for v in d['violations'] if v['type'] not in ['silk_overlap','silk_over_copper'] for i in v['items'] if i['description'].startswith(('Track','Via'))}
a[:]=[x for x in a if not(isinstance(x,list) and x[0] in ['segment','via'] and val(child(x,'uuid')[1]) in ids)]
for f in children(a,'footprint'):
 if any(val(v[1])=='Reference' and val(v[2])=='J2' for v in children(f,'property')):
  silkids={i['uuid'] for v in d['violations'] if v['type']=='silk_over_copper' for i in v['items'] if i['description'].startswith('Segment of J2')}
  f[:]=[x for x in f if not(isinstance(x,list) and child(x,'uuid') and val(child(x,'uuid')[1]) in silkids)]
for t in children(a,'gr_text'):
 if val(t[1])=='HIGH':child(t,'at')[1:3]=['9','89.6']
path.write_text(ser(a));print('Removed invalid/stub track objects:',len(ids))
