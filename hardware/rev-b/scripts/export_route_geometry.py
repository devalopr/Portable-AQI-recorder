from pathlib import Path
import pcbnew as p,json
b=p.LoadBoard('hardware/rev-b/battery/AQI_Battery_Compact.kicad_pcb');objects=[];fps=[]
def xy(a):return [p.ToMM(a.x),p.ToMM(a.y)]
def rect(r):return [p.ToMM(v) for v in [r.GetLeft(),r.GetTop(),r.GetRight(),r.GetBottom()]]
for f in b.GetFootprints():
 fps.append(dict(ref=f.GetReference(),layer=f.GetLayer(),box=rect(f.GetBoundingBox(False,False))))
 for a in f.Pads():
  objects.append(dict(type='pad',ref=f.GetReference(),pin=a.GetNumber(),net=a.GetNetname(),layers=[l for l in [0,2] if a.IsOnLayer(l)],box=[v+(-.1 if i<2 else .1) for i,v in enumerate(rect(a.GetBoundingBox()))] if a.GetAttribute()==p.PAD_ATTRIB_NPTH else rect(a.GetBoundingBox()),xy=xy(a.GetPosition())))
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):objects.append(dict(type='via',uuid=t.m_Uuid.AsString(),net=t.GetNetname(),layers=[0,2],xy=xy(t.GetPosition()),r=p.ToMM(t.GetWidth(p.F_Cu))/2))
 else:objects.append(dict(type='track',uuid=t.m_Uuid.AsString(),net=t.GetNetname(),layers=[t.GetLayer()],a=xy(t.GetStart()),z=xy(t.GetEnd()),r=p.ToMM(t.GetWidth())/2))
outline=[(1.5,0),(24.7,0),(26.2,1.5),(26.2,86.5),(24.7,88),(1.5,88),(0,86.5),(0,1.5)]
Path('/tmp/aqi-battery-geometry.json').write_text(json.dumps(dict(objects=objects,footprints=fps,outline=outline)))
