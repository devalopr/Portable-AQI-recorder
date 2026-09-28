"""DSN/SES exchange and ground fill; does not change component placement."""
from pathlib import Path
import json,sys,re
import pcbnew as p
root=Path(sys.argv[1]);mode=sys.argv[2];d=json.loads((root/'design.json').read_text());name=d['name'];path=root/(name+'.kicad_pcb');project_path=root/(name+'.kicad_pro');saved_project=project_path.read_text();b=p.LoadBoard(str(path));review=root/'review';review.mkdir(exist_ok=True)
if mode=='export':
 for z in list(b.Zones()):
  if not z.GetIsRuleArea():b.Remove(z)
 assert p.ExportSpecctraDSN(b,str(review/(name+'.dsn')))
 f=review/(name+'.dsn');s=f.read_text()
 # Reserve inner layer 1 for the return plane; route on the other three layers.
 s=s.replace('(layer In1.Cu\n      (type signal)','(layer In1.Cu\n      (type power)')
 s=s.replace('(clearance 200)','(clearance 150)').replace('(clearance 50 (type smd_smd))','(clearance 150 (type smd_smd))')
 f.write_text(s)
elif mode=='import':
 assert (review/(name+'.ses')).stat().st_size>1000,'Empty router output'
 assert p.ImportSpecctraSES(b,str(review/(name+'.ses')))
 p.SaveBoard(str(path),b)
elif mode=='fill':
 for z in list(b.Zones()):
  if not z.GetIsRuleArea():b.Remove(z)
 ground=next(n.GetNetCode() for n in b.GetNetsByName().values() if n.GetNetname()=='GND')
 for ly in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  z=p.ZONE(b);z.SetLayer(ly);z.SetNetCode(ground);z.SetLocalClearance(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinThickness(p.FromMM(.15));poly=z.Outline();poly.NewOutline()
  for x,y in [(.4,.4),(d['width']-.4,.4),(d['width']-.4,d['height']-.4),(.4,d['height']-.4)]:poly.Append(p.FromMM(x),p.FromMM(y))
  b.Add(z)
 p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
print(mode,name)

project_path.write_text(saved_project)
