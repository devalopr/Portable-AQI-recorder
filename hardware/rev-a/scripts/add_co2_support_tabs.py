"""One-time change from open island notches to enclosed slots with 1.5mm outer tabs."""
from pathlib import Path
import sys,json
import pcbnew as p
from kicad_common import parse,ser,child
root=Path('hardware/rev-a/main');f=root/'AQI_Main.kicad_pcb';pro=f.with_suffix('.kicad_pro');saved=pro.read_text()
backup=Path('/tmp/aqi-main-before-support-tabs.kicad_pcb');backup.write_bytes(f.read_bytes())
s=parse(f.read_text());s[:]=[t for t in s if not(isinstance(t,list) and t[0] in ['gr_line','gr_arc'] and child(t,'layer') and 'Edge.Cuts' in str(child(t,'layer')))];f.write_text(ser(s));b=p.LoadBoard(str(f));mm=p.FromMM
loops=[[(1.5,0),(42.5,0),(44,1.5),(44,78.5),(42.5,80),(1.5,80),(0,78.5),(0,1.5)],[(42.5,50),(24,50),(24,56),(27,56),(27,51),(42.5,51)],[(42.5,63),(27,63),(27,58),(24,58),(24,64),(42.5,64)]]
for loop in loops:
 for a,c in zip(loop,loop[1:]+loop[:1]):
  sh=p.PCB_SHAPE();sh.SetShape(p.SHAPE_T_SEGMENT);sh.SetStart(p.VECTOR2I(mm(a[0]),mm(a[1])));sh.SetEnd(p.VECTOR2I(mm(c[0]),mm(c[1])));sh.SetLayer(p.Edge_Cuts);sh.SetWidth(mm(.05));b.Add(sh)
for y in [50,63]:
 for ly in [p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu]:
  z=p.ZONE(b);z.SetLayer(ly);z.SetIsRuleArea(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(True);poly=z.Outline();poly.NewOutline()
  for x,yy in [(42.2,y-.2),(44,y-.2),(44,y+1.2),(42.2,y+1.2)]:poly.Append(mm(x),mm(yy))
  b.Add(z)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(f),b);pro.write_text(saved)
report=root/'review/thermal-layout.json';d=json.loads(report.read_text());d['outer_support_tabs']={'count':2,'width_mm':1.5,'span_mm':1,'x_mm':[42.5,44],'y_mm':[[50,51],[63,64]],'copper':'Prohibited on all four layers','purpose':'Permanent mechanical support, not breakaway tabs; increases FR4 thermal conduction'};report.write_text(json.dumps(d,indent=2)+'\n')
