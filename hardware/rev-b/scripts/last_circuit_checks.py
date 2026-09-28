from pathlib import Path
import json
import pcbnew as p
from kicad_common import Project,uid
r=Path(__file__).resolve().parents[1]/'battery';dp=r/'design.json';d=json.loads(dp.read_text());D={c['ref']:c for c in d['components']};D['J7']['nets'].update(A12='GND',B12='GND')
if 'C24' not in D:
 d['components'].append(dict(ref='C24',lib='Device:C',value='100nF 16V X7R',mpn='',fp='Capacitor_SMD:C_0603_1608Metric',nets={'1':'CELL_POS','2':'GND'},xy=[17,34.4],sch=[650,502],side='back',rot=0,note='Fuel gauge local bypass'))
dp.write_text(json.dumps(d,indent=2)+'\n');proj=Project(dp);proj.schematic();sp=r/(d['name']+'.kicad_sch');sp.write_text(sp.read_text().replace('(paper "A2")','(paper "A1")'));pp=r/(d['name']+'.kicad_pro');pro=pp.read_text();b=p.LoadBoard(str(r/(d['name']+'.kicad_pcb')));gnd=b.FindNet('GND');cell=b.FindNet('CELL_POS')
for f in b.GetFootprints():
 if f.GetReference()=='J7':
  for pad in f.Pads():
   if pad.GetNumber() in ['A12','B12']:pad.SetNet(gnd)
if not any(f.GetReference()=='C24' for f in b.GetFootprints()):
 f=p.FootprintLoad('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Capacitor_SMD.pretty','C_0603_1608Metric');f.SetReference('C24');f.SetValue('100nF 16V X7R');f.SetPath(p.KIID_PATH('/'+proj.root+'/'+uid(d['name']+'/C24')));f.SetPosition(p.VECTOR2I(p.FromMM(17),p.FromMM(34.4)));b.Add(f);f.Flip(f.GetPosition(),False);f.SetOrientationDegrees(0);f.Reference().SetVisible(False);f.Value().SetVisible(False)
 for pad in f.Pads():pad.SetNet(cell if pad.GetNumber()=='1' else gnd)
p.SaveBoard(str(r/(d['name']+'.kicad_pcb')),b);pp.write_text(pro)
