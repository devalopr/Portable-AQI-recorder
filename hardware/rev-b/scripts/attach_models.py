from pathlib import Path
import json
import pcbnew as p
from kicad_common import Project
r=Path(__file__).resolve().parents[1]/'battery';dp=r/'design.json';d=json.loads(dp.read_text());name=d['name'];pp=r/(name+'.kicad_pro');pro=pp.read_text();D={c['ref']:c for c in d['components']}
D['J7']['nets']={'A1':'GND','A9':'USB_VBUS_OUT','A5':'OUT_CC1','B1':'GND','B9':'USB_VBUS_OUT','B5':'OUT_CC2','SH':'GND'}
dp.write_text(json.dumps(d,indent=2)+'\n');b=p.LoadBoard(str(r/(name+'.kicad_pcb')))
models={'J1':'USB4110_envelope.step','U6':'TUSB320_envelope.step','U7':'TUSB320_envelope.step','U4':'MAX17048_envelope.step','D1':'RGB_envelope.step'}
net=b.FindNet('/USB_VBUS_OUT')
for f in b.GetFootprints():
 if f.GetReference() in models:
  f.Models().clear();m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/lib/3d/'+models[f.GetReference()];f.Add3DModel(m)
 if f.GetReference()=='J7':
  for pad in f.Pads():
   if pad.GetNumber() in ['A9','B9']:pad.SetNet(net)
p.SaveBoard(str(r/(name+'.kicad_pcb')),b);pp.write_text(pro)
Project(dp).schematic();sp=r/(name+'.kicad_sch');sp.write_text(sp.read_text().replace('(paper "A2")','(paper "A1")'))
