"""Move auxiliary holes/LED; add an M3 edge notch. Preserve existing routing."""
from pathlib import Path
import json,math
from kicad_common import Project,parse,ser,child,val,uid
import pcbnew as p
r=Path(__file__).resolve().parents[1]/'battery';dp=r/'design.json';d=json.loads(dp.read_text());D={c['ref']:c for c in d['components']};path=r/(d['name']+'.kicad_pcb');pp=path.with_suffix('.kicad_pro');pro=pp.read_text();b=p.LoadBoard(str(path));mm=p.FromMM
oldpads=[a.GetBoundingBox() for f in b.GetFootprints() if f.GetReference() in ['J8','J9','D1'] for a in f.Pads()];remove=set()
for t in b.GetTracks():
 if t.GetNetname() in ['LED_RED','LED_GREEN','LED_BLUE','/LED_RED','/LED_GREEN','/LED_BLUE']:remove.add(t.m_Uuid.AsString());continue
 pts=[t.GetPosition()] if isinstance(t,p.PCB_VIA) else [t.GetStart(),t.GetEnd()]
 if any(bb.Contains(v) for bb in oldpads for v in pts):remove.add(t.m_Uuid.AsString())
 # A screw/washer occupies both faces; reserve a 3.4 mm radius.
 if isinstance(t,p.PCB_VIA):near=math.dist([p.ToMM(t.GetPosition().x),p.ToMM(t.GetPosition().y)],[26.2,85.3])<3.7
 else:
  a,z=t.GetStart(),t.GetEnd();a=[p.ToMM(a.x),p.ToMM(a.y)];z=[p.ToMM(z.x),p.ToMM(z.y)];dx=z[0]-a[0];dy=z[1]-a[1];u=max(0,min(1,((26.2-a[0])*dx+(85.3-a[1])*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0;near=math.dist([a[0]+u*dx,a[1]+u*dy],[26.2,85.3])<3.5
 if near:remove.add(t.m_Uuid.AsString())
raw=parse(path.read_text());raw[:]=[x for x in raw if not(isinstance(x,list) and (x[0]=='zone' or (x[0] in ['segment','via'] and val(child(x,'uuid')[1]) in remove) or (x[0]=='gr_line' and val(child(x,'layer')[1])=='Edge.Cuts')))];path.write_text(ser(raw));b=p.LoadBoard(str(path))
for ref,xy,nets,value in [('J8',[2.7,2.4],{'1':'BOOST_5V','2':'GND'},'5V / GND'),('J9',[20.96,2.4],{'1':'GND','2':'GEN_3V3'},'GND / 3V3')]:
 c=D[ref];c.update(lib='Connector_Generic:Conn_01x02',fp='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',nets=nets,value=value,xy=xy,rot=90,side='front',note='Bare plated holes, horizontal row clear of holder. Read from holder face: 5V GND USB-C GND 3V3.')
 old=next(f for f in b.GetFootprints() if f.GetReference()==ref);oldpath=old.GetPath();b.Remove(old);f=p.FootprintLoad('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_PinHeader_2.54mm.pretty','PinHeader_1x02_P2.54mm_Vertical');b.Add(f);f.SetReference(ref);f.SetValue(value);f.SetPath(oldpath);f.SetPosition(p.VECTOR2I(mm(xy[0]),mm(xy[1])));f.SetOrientationDegrees(90);f.SetDNP(True);f.Models().clear();f.Reference().SetVisible(False);f.Value().SetVisible(False)
 for a in f.Pads():
  n=nets[a.GetNumber()];net=b.FindNet(n) or b.FindNet('/'+n);a.SetNet(net)
D['D1'].update(xy=[4,85.5],side='front',rot=0)
f=next(f for f in b.GetFootprints() if f.GetReference()=='D1');f.Flip(f.GetPosition(),False);f.SetOrientationDegrees(0);f.SetPosition(p.VECTOR2I(mm(4),mm(85.5)))
# Remove old auxiliary labels; place new labels on the holder face.
for t in list(b.GetDrawings()):
 if isinstance(t,p.PCB_TEXT) and t.GetText() in ['GND','5V','3V3']:b.Remove(t)
for text,x in [('5V',2.7),('GND',5.24),('GND',20.96),('3V3',23.5)]:
 t=p.PCB_TEXT(b);t.SetText(text);t.SetPosition(p.VECTOR2I(mm(x),mm(4.05)));t.SetLayer(p.F_SilkS);t.SetTextSize(p.VECTOR2I(mm(.8),mm(.8)));t.SetTextThickness(mm(.12));b.Add(t)
pts=[(1.5,0),(24.7,0),(26.2,1.5),(26.2,83.6)]
def line(a,z):
 s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(p.VECTOR2I(mm(a[0]),mm(a[1])));s.SetEnd(p.VECTOR2I(mm(z[0]),mm(z[1])));s.SetLayer(p.Edge_Cuts);s.SetWidth(mm(.05));b.Add(s)
for a,z in zip(pts,pts[1:]):line(a,z)
s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_ARC);s.SetArcGeometry(p.VECTOR2I(mm(26.2),mm(83.6)),p.VECTOR2I(mm(24.5),mm(85.3)),p.VECTOR2I(mm(26.2),mm(87)));s.SetLayer(p.Edge_Cuts);s.SetWidth(mm(.05));b.Add(s)
pts=[(26.2,87),(26.2,87.5),(25.7,88),(1.5,88),(0,86.5),(0,1.5),(1.5,0)]
for a,z in zip(pts,pts[1:]):line(a,z)
for layer in [p.F_Cu,p.B_Cu]:
 z=p.ZONE(b);z.SetLayer(layer);z.SetIsRuleArea(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(True);z.SetDoNotAllowFootprints(True);z.SetDoNotAllowZoneFills(True);poly=z.Outline();poly.NewOutline()
 for i in range(65):
  a=math.pi/2+i*math.pi/64;poly.Append(mm(26.2+3.4*math.cos(a)),mm(85.3+3.4*math.sin(a)))
 b.Add(z)
d['mechanical_revision']={'header_row':'holder face, y=2.4mm: 5V GND USB-C GND 3V3','mount':'3.4mm diameter semicircular notch at right edge y85.3mm; washer/head clearance radius3.4mm','holder_alternative':'Robocraze generic 77x21x15; mounting and cell-gap dimensions pending, not qualified as Keystone1042 replacement'}
dp.write_text(json.dumps(d,indent=2)+'\n');p.SaveBoard(str(path),b);pp.write_text(pro);Project(dp).schematic();sp=path.with_suffix('.kicad_sch');sp.write_text(sp.read_text().replace('(paper "A2")','(paper "A1")'));print('Updated header row, LED and M3 notch; removed',len(remove),'affected route objects')
for f in b.GetFootprints():
 if f.GetReference() in ['J8','J9']:print(f.GetReference(),[(a.GetNumber(),p.ToMM(a.GetPosition().x),p.ToMM(a.GetPosition().y),a.GetNetname()) for a in f.Pads()])
