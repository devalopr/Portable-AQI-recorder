import pcbnew as p,json
from pathlib import Path
root=Path('hardware/rev-a/main');path=root/'AQI_Main.kicad_pcb';pro=root/'AQI_Main.kicad_pro';saved=pro.read_text();b=p.LoadBoard(str(path));bad=[(28.2,50.6475),(33.5,55)]
def xy(pt):return [p.ToMM(pt.x),p.ToMM(pt.y)]
objects=[]
for f in b.GetFootprints():
 for q in f.Pads():
  box=q.GetBoundingBox();objects.append(dict(type='pad',net=q.GetNetname(),layers=[i for i in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu] if q.IsOnLayer(i)],box=[p.ToMM(box.GetLeft()),p.ToMM(box.GetTop()),p.ToMM(box.GetRight()),p.ToMM(box.GetBottom())]))
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):objects.append(dict(type='via',net=t.GetNetname(),layers=[0,4,6,2],xy=xy(t.GetPosition()),r=p.ToMM(t.GetWidth(p.F_Cu))/2))
 else:objects.append(dict(type='track',net=t.GetNetname(),layers=[t.GetLayer()],a=xy(t.GetStart()),z=xy(t.GetEnd()),r=p.ToMM(t.GetWidth())/2))
Path('/tmp/aqi-obstacles.json').write_text(json.dumps(dict(objects=objects,F=p.F_Cu,B=p.B_Cu)))
p.SaveBoard(str(path),b);pro.write_text(saved)
