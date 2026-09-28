from pathlib import Path
import json,sys
from kicad_common import Project
r=Path(__file__).resolve().parents[1]/'battery';p=r/'design.json';d=json.loads(p.read_text());D={c['ref']:c for c in d['components']}
D['J1']['xy']=[19.6,83.29];D['D1'].update(xy=[2,44],side='back');D['TP3']['xy']=[2,64]
# Local version uses ordinary 0.30mm drilled thermal vias for economical fabrication.
from kicad_common import parse,ser,children,child,q
source=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Package_DFN_QFN.pretty/Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias.kicad_mod')
f=parse(source.read_text());f[1]=q('BQ25606_RGE_ThermalVias_03')
for pad in children(f,'pad'):
 if pad[2]=='thru_hole':child(pad,'drill')[1]='0.3';child(pad,'size')[1:]=['0.6','0.6']
(r/'lib/AQI.pretty/BQ25606_RGE_ThermalVias_03.kicad_mod').write_text(ser(f))
D['U1']['fp']='AQI:BQ25606_RGE_ThermalVias_03'
p.write_text(json.dumps(d,indent=2)+'\n');Project(p).board()
