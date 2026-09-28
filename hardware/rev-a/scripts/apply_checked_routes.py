from pathlib import Path
import sys,json,pcbnew as p
root=Path('hardware/rev-a/main');path=root/'AQI_Main.kicad_pcb';pro=root/'AQI_Main.kicad_pro';saved=pro.read_text();b=p.LoadBoard(str(path));nets={n.GetNetname():n.GetNetCode() for n in b.GetNetsByName().values()};mm=p.FromMM
via_keys={(t.GetNetname(),t.GetPosition().x,t.GetPosition().y) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)}
for route in json.loads(Path(sys.argv[1]).read_text()):
 for a,z in zip(route['path'],route['path'][1:]):
  pa=p.VECTOR2I(mm(a[0]),mm(a[1]));pz=p.VECTOR2I(mm(z[0]),mm(z[1]))
  if a[2]!=z[2]:
   key=(route['net'],pa.x,pa.y)
   if key in via_keys:continue
   t=p.PCB_VIA(b);t.SetPosition(pa);t.SetWidth(mm(.6));t.SetDrill(mm(.3));t.SetLayerPair(p.F_Cu,p.B_Cu);via_keys.add(key)
  else:
   if pa==pz:continue
   t=p.PCB_TRACK(b);t.SetStart(pa);t.SetEnd(pz);t.SetLayer(a[2]);t.SetWidth(mm(route['width']))
  t.SetNetCode(nets[route['net']]);b.Add(t)
p.SaveBoard(str(path),b);pro.write_text(saved)
