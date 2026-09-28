"""Align the catalogue shell model to the manufacturer's seating plane and footprint.
SHOUHAN drawing p6: shell height3.16mm, shell length7.35mm.
Catalogue STEP shell envelope: Y=-3.665..3.665,Z top=1.58;
footprint shell mouth is local Y=+5 (STEP Y=-5), seating planeZ=0.
This model is a shell-envelope reference, not a verified 16-contact model.
"""
from pathlib import Path
from kicad_common import parse,ser,children,child,val
R=Path(__file__).resolve().parents[1]/'integrated-power'
paths=[R/'AQI_IP5310_Power.kicad_pcb',R/'lib/AQI_Power.pretty/USB-C-SMD_TYPE-C-16PIN-2MD-073.kicad_mod']
for path in paths:
 a=parse(path.read_text());fps=[a] if path.suffix=='.kicad_mod' else [f for f in children(a,'footprint') if any(val(t[1])=='Reference' and val(t[2])=='J1' for t in children(f,'property'))]
 assert len(fps)==1
 m=child(fps[0],'model');child(child(m,'offset'),'xyz')[1:]=['0','-1.335','1.58'];path.write_text(ser(a)+'\n')
p=Path(__file__).with_name('prepare_catalog_footprints.py');s=p.read_text();needle=" for t in children(f,'fp_text'):"
if 'offset correction for the centered STEP' not in s:s=s.replace(needle," # Seating offset correction for the centered STEP shell model.\n if inp:\n  for m in children(f,'model'):child(child(m,'offset'),'xyz')[1:]=['0','-1.335','1.58']\n"+needle);p.write_text(s)
print('J1 model aligned; footprint/pads/routing unchanged')
