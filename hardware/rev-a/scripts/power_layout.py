"""Pre-route short switch connections on the component side before signal routing."""
from pathlib import Path
import sys,json
import pcbnew as p
folder=Path(sys.argv[1]);d=json.loads((folder/'design.json').read_text());name=d['name'];f=folder/(name+'.kicad_pcb');pro=folder/(name+'.kicad_pro');saved=pro.read_text();b=p.LoadBoard(str(f));pads={(f.GetReference(),pad.GetNumber()):pad for f in b.GetFootprints() for pad in f.Pads() if pad.GetNumber()}
def link(a,z):
 a=pads[a];z=pads[z];start=a.GetPosition();end=z.GetPosition();assert a.GetNetCode()==z.GetNetCode()
 # Short pad escape sized for 0.5/0.65-mm IC pitch, then a wider switch trace.
 x,y=p.ToMM(start.x),p.ToMM(start.y);ex,ey=p.ToMM(end.x),p.ToMM(end.y);sgn=1 if ex>x else -1
 points=[(x,y),(x+sgn*.65,y),(ex-sgn*.6,ey),(ex,ey)]
 for i,(a1,b1) in enumerate(zip(points,points[1:])):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a1[0]),p.FromMM(a1[1])));t.SetEnd(p.VECTOR2I(p.FromMM(b1[0]),p.FromMM(b1[1])));t.SetWidth(p.FromMM(.2 if i==0 else .5));t.SetNetCode(a.GetNetCode());t.SetLayer(p.B_Cu);t.SetLocked(True);b.Add(t)
if name=='AQI_Main':
 link(('U5','7'),('L1','1'));link(('U6','7'),('L2','1'))
else:
 link(('U2','5'),('L1','2'));link(('U3','2'),('L2','2'));link(('U3','4'),('L2','1'))
p.SaveBoard(str(f),b);pro.write_text(saved)
