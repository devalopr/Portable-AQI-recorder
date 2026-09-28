from pathlib import Path
import pcbnew as p,json
for folder,name in [('main','AQI_Main'),('battery','AQI_Battery')]:
 root=Path('hardware/rev-a')/folder;pro=root/(name+'.kicad_pro');saved=pro.read_text();b=p.LoadBoard(str(root/(name+'.kicad_pcb')))
 if folder=='battery':
  for t in b.GetDrawings():
   if isinstance(t,p.PCB_TEXT) and t.GetText()=='CELL +':t.SetPosition(p.VECTOR2I(p.FromMM(22),p.FromMM(87.5)))
  ground=next(n.GetNetCode() for n in b.GetNetsByName().values() if n.GetNetname()=='GND')
  for x,y in [(16.4125,59.6),(17.2125,59.6),(16.4125,60.4),(17.2125,60.4),(17.8125,26.55),(17.8125,27.45)]:
   v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(ground);b.Add(v)
 else:
  for f in b.GetFootprints():
   if f.GetReference()=='R30':f.SetValue('1MR')
 p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(root/(name+'.kicad_pcb')),b);pro.write_text(saved)
