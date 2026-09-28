"""Review-only model population. Electrical PCB and BOM are not modified."""
from pathlib import Path
import sys,uuid,shutil
from kicad_common import parse,ser,child,children,val
R=Path(__file__).resolve().parents[1]/'integrated-power';out=R/'mechanical-fit'
s=(R/'AQI_IP5310_Power.kicad_pcb').read_text().replace('${KIPRJMOD}/lib/','${KIPRJMOD}/../lib/')
b=parse(s)
def model(name):return parse('(model "${KIPRJMOD}/models/'+name+'" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
for f in children(b,'footprint'):
 ref=next((val(a[2]) for a in children(f,'property') if val(a[1])=='Reference'),None)
 if ref in ['J8','J9','J10','J2']:
  f[:]=[a for a in f if not(isinstance(a,list) and a[0]=='model')]
  if ref=='J2':f.append(model('Holder_77p5x21p5_PROVISIONAL.step'))
  else:
   attr=child(f,'attr');attr[:]=[v for v in attr if v!='dnp']
   f.extend([model('Header_1x02.step'),model('Dupont_2way_envelope.step')])
for i,(x,y) in enumerate([(0,5.2),(26.5,5.2),(0,90),(26.5,90)],1):
 f=parse(f'(footprint "Mechanical_fit:M3x8" (layer "F.Cu") (uuid "{uuid.uuid4()}") (at {x} {y}) (property "Reference" "MH{i}" (at 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness .15)))) (property "Value" "M3x8 ISO4762 FIT ONLY" (at 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness .15)))) (attr board_only exclude_from_pos_files exclude_from_bom))')
 f.append(model('M3x8_ISO4762.step'));b.append(f)
(out/'AQI_Power_Mechanical_Fit.kicad_pcb').write_text(ser(b))
shutil.copy2(R/'AQI_IP5310_Power.kicad_pro',out/'AQI_Power_Mechanical_Fit.kicad_pro')
print(out/'AQI_Power_Mechanical_Fit.kicad_pcb')
