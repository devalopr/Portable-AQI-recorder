from pathlib import Path
import pcbnew as p,json
b=p.LoadBoard('hardware/rev-a/main/AQI_Main.kicad_pcb');objects=[];fps=[]
def xy(a):return [p.ToMM(a.x),p.ToMM(a.y)]
def rect(r):return [p.ToMM(v) for v in [r.GetLeft(),r.GetTop(),r.GetRight(),r.GetBottom()]]
for f in b.GetFootprints():
 fps.append(dict(ref=f.GetReference(),layer=f.GetLayer(),box=rect(f.GetBoundingBox(False,False))))
 for a in f.Pads():
  objects.append(dict(type='pad',ref=f.GetReference(),pin=a.GetNumber(),net=a.GetNetname(),layers=[l for l in [0,2,4,6] if a.IsOnLayer(l)],box=rect(a.GetBoundingBox()),xy=xy(a.GetPosition())))
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):objects.append(dict(type='via',uuid=t.m_Uuid.AsString(),net=t.GetNetname(),layers=[0,2,4,6],xy=xy(t.GetPosition()),r=p.ToMM(t.GetWidth(p.F_Cu))/2))
 else:objects.append(dict(type='track',uuid=t.m_Uuid.AsString(),net=t.GetNetname(),layers=[t.GetLayer()],a=xy(t.GetStart()),z=xy(t.GetEnd()),r=p.ToMM(t.GetWidth())/2))
outline=[(1.5,0),(42.5,0),(44,1.5),(44,50),(24,50),(24,56),(27,56),(27,51),(44,51),(44,63),(27,63),(27,58),(24,58),(24,64),(44,64),(44,78.5),(42.5,80),(1.5,80),(0,78.5),(0,1.5)]
Path('/tmp/aqi-route-geometry.json').write_text(json.dumps(dict(objects=objects,footprints=fps,outline=outline)))
