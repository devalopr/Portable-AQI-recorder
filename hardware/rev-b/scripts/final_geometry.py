import sys,json
from pathlib import Path
from kicad_common import Project
import pcbnew as p
r=Path(__file__).resolve().parents[1]/'battery';dp=r/'design.json';d=json.loads(dp.read_text());d['width']=26.2;dp.write_text(json.dumps(d,indent=2)+'\n')
Project(dp).settings()
pp=r/(d['name']+'.kicad_pro');pro=json.loads(pp.read_text());pro['net_settings']['netclass_patterns'] += [dict(netclass='Power',pattern='/'+n) for n in ['CELL_POS','CELL_NEG','PROT_CENTER','CHG_SYS','CHG_SW','CHG_PMID','BOOST_SW','BOOST_5V','BOOST_L1','BOOST_L2','GEN_3V3','USB_VBUS_IN','USB_VBUS_OUT']]
# Moderate width plus copper pours; high-current trunks need subsequent manual review.
for c in pro['net_settings']['classes']:
 if c['name']=='Power':c['track_width']=.5
pro=json.dumps(pro,indent=2)
f=r/(d['name']+'.kicad_pcb');b=p.LoadBoard(str(f));mm=p.FromMM
for sh in b.GetDrawings():
 if sh.GetLayer()==p.Edge_Cuts:
  for get,setter in [(sh.GetStart,sh.SetStart),(sh.GetEnd,sh.SetEnd)]:
   v=get()
   if p.ToMM(v.x)>20:v.x+=mm(.5);setter(v)
for fp in b.GetFootprints():
 if fp.GetReference()=='U9':fp.SetLocalClearance(mm(.15))
# Hide stock internal numbering that collided with nearby parts.
for fp in b.GetFootprints():
 if fp.GetReference()=='D1':
  for item in fp.GraphicalItems():
   if hasattr(item,'GetText'):item.SetLayer(p.B_Fab)
p.SaveBoard(str(f),b);pp.write_text(pro)
# Refresh schematic only, preserving the reviewed A1 layout.
Project(dp).schematic();sp=r/(d['name']+'.kicad_sch');sp.write_text(sp.read_text().replace('(paper "A2")','(paper "A1")'))
