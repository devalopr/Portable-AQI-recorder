"""Create the user-requested lower-antenna placement in an isolated revision only."""
from pathlib import Path
import sys,json
import pcbnew as p
from kicad_common import parse,ser,child,val
root=Path('hardware/rev-a/lower-antenna-revision');f=root/'AQI_Main.kicad_pcb';pro=f.with_suffix('.kicad_pro');saved=pro.read_text()
# Start only from the checked main board. Keep its critical buck and sensor-neck routes.
x=parse(Path('hardware/rev-a/main/AQI_Main.kicad_pcb').read_text());kept=[]
for i in x:
 if not isinstance(i,list):kept.append(i);continue
 if i[0] in ['segment','via']:
  pts=[child(i,k) for k in (['at'] if i[0]=='via' else ['start','end'])];coords=[(float(q[1]),float(q[2])) for q in pts]
  neck=all(23.5<=a<=44 and 50.5<=b<=63.5 for a,b in coords)
  locked=any(t=='locked' for t in i)
  if not(neck or locked):continue
 if i[0]=='zone':
  # Keep slot/thermal rules; remove copper fills and the former upper-right antenna rule.
  if child(i,'keepout') is None:continue
  poly=child(i,'polygon');txt=ser(poly) if poly else ''
  if '(xy 37 10)' in txt or '(xy 44 27)' in txt:continue
 kept.append(i)
f.write_text(ser(kept));b=p.LoadBoard(str(f));F={q.GetReference():q for q in b.GetFootprints()};mm=p.FromMM
moves={'U1':(9.3,71.2,0),'C1':(1.3,67.5,90),'C2':(1.3,71,90),'C3':(1.3,64,90),'J1':(37.3,75.29,0),'J2':(23.8,76,0),'SW4':(41.7,69,-90),'J5':(22,16.85,0),'U10':(22,6,180),'C18':(28.5,6,180),'R26':(21,10.5,180),'R28':(25.5,10.5,180),'C19':(17,10.5,180)}
for ref,(x,y,a) in moves.items():F[ref].SetOrientationDegrees(a);F[ref].SetPosition(p.VECTOR2I(mm(x),mm(y)))
for ly in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
 z=p.ZONE(b);z.SetLayer(ly);z.SetIsRuleArea(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(True);poly=z.Outline();poly.NewOutline()
 for x,y in [(0,73.8),(16.2,73.8),(16.2,80),(0,80)]:poly.Append(mm(x),mm(y))
 b.Add(z)
for t in b.GetTracks():t.SetLocked(True)
p.SaveBoard(str(f),b);pro.write_text(saved)
d=json.loads((root/'design.json').read_text());d['keepouts']=[[[0,73.8],[16.2,73.8],[16.2,80],[0,80]]]
for c in d['components']:
 if c['ref'] in moves:
  x,y,a=moves[c['ref']];c.update(xy=[x,y],rot=(180-a)%360 if F[c['ref']].GetLayer()==p.B_Cu else a)
(root/'design.json').write_text(json.dumps(d,indent=2)+'\n')
for ref in ['U1','SW4','J1','J2','J5']:
 fp=F[ref];print(ref,fp.GetOrientationDegrees(),p.ToMM(fp.GetPosition()))
 if ref=='U1':
  for a in fp.Pads():
   if a.GetNetname() in ['+3V2','/MCU_EN']:print(a.GetNumber(),a.GetNetname(),p.ToMM(a.GetPosition()))
print('Retained critical tracks/vias',len(b.GetTracks()))
