"""Final explicit power bridges, track neck sizes, and current-distribution zones."""
from pathlib import Path
import sys,json
import pcbnew as p
folder=Path(sys.argv[1]);d=json.loads((folder/'design.json').read_text());name=d['name'];path=folder/(name+'.kicad_pcb');pro=folder/(name+'.kicad_pro');saved=pro.read_text();b=p.LoadBoard(str(path));mm=p.FromMM
nets={n.GetNetname().lstrip('/'):n.GetNetCode() for n in b.GetNetsByName().values()}
def point(x,y):return p.VECTOR2I(mm(x),mm(y))
def track(net,a,z,layer=p.B_Cu,width=.2):
 t=p.PCB_TRACK(b);t.SetStart(point(*a));t.SetEnd(point(*z));t.SetWidth(mm(width));t.SetNetCode(nets[net]);t.SetLayer(layer);b.Add(t)
def via(net,xy):
 v=p.PCB_VIA(b);v.SetPosition(point(*xy));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(nets[net]);b.Add(v)
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetWidth()<mm(.15):t.SetWidth(mm(.15))
if name=='AQI_Main':
 track('+5V_SYS',(15.74,56.8375),(14.26,56.8375))
 track('+3V2',(27.1125,50.6475),(28.2,50.6475),width=.15);via('+3V2',(28.2,50.6475))
 track('+3V2',(32.45,55),(33.5,55));via('+3V2',(33.5,55))
 zones=[('+5V_SW',p.In2_Cu,1,(.5,.5,43.5,79.5)),('+3V2',p.F_Cu,2,(27.7,50.1,34.2,55.6))]
else:
 zones=[('CHG_SYS',p.In2_Cu,1,(.5,.5,43.5,89.5)),('CELL_POS',p.F_Cu,2,(12,52,33,81)),('CELL_NEG',p.B_Cu,2,(19,4,26,12))]
 for t in b.GetDrawings():
  if isinstance(t,p.PCB_TEXT) and t.GetText()=='CELL +':t.SetPosition(point(22,85))
for net,ly,priority,rect in zones:
 z=p.ZONE(b);z.SetLayer(ly);z.SetNetCode(nets[net]);z.SetAssignedPriority(priority);z.SetLocalClearance(mm(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinThickness(mm(.15));poly=z.Outline();poly.NewOutline();x,y,r,bot=rect
 for a,c in [(x,y),(r,y),(r,bot),(x,bot)]:poly.Append(mm(a),mm(c))
 b.Add(z)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);pro.write_text(saved)
