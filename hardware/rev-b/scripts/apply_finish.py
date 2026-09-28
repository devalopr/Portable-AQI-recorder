from pathlib import Path
import pcbnew as p,json
from kicad_common import parse,ser,children
r=Path(__file__).resolve().parents[1]/'battery';path=r/'AQI_Battery_Compact.kicad_pcb';pp=path.with_suffix('.kicad_pro');pro=pp.read_text();raw=parse(path.read_text())
for z in children(raw,'zone'):z[:]=[x for x in z if not(isinstance(x,list) and x[0]=='filled_polygon')]
path.write_text(ser(raw));b=p.LoadBoard(str(path));mm=p.FromMM
for route in json.load(open('/tmp/aqi-battery-finish.json')):
 net=b.FindNet(route['net']);assert net
 for a,z in zip(route['path'],route['path'][1:]):
  if a[2]!=z[2]:
   if any(isinstance(v,p.PCB_VIA) and v.GetNetname()==route["net"] and abs(p.ToMM(v.GetPosition().x)-a[0])<.001 and abs(p.ToMM(v.GetPosition().y)-a[1])<.001 for v in b.GetTracks()):continue
   t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(mm(a[0]),mm(a[1])));t.SetWidth(mm(route.get("via_diameter",.6)));t.SetDrill(mm(route.get("via_drill",.3)));t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetIsFree(True)
  elif a[:2]!=z[:2]:
   t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(mm(a[0]),mm(a[1])));t.SetEnd(p.VECTOR2I(mm(z[0]),mm(z[1])));t.SetLayer(a[2]);t.SetWidth(mm(route['width']))
  else:continue
  t.SetNet(net);b.Add(t)
p.SaveBoard(str(path),b);pp.write_text(pro)
