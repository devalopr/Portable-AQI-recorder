"""Apply the requested front/right connector arrangement to existing footprints.
One-time construction step: removes old routing. Never run on a finished board.
"""
from pathlib import Path
import json,sys,math,shutil
import pcbnew as p
from kicad_common import parse,ser,child
root=Path('hardware/rev-a/main');path=root/'AQI_Main.kicad_pcb';pro=root/'AQI_Main.kicad_pro';saved=pro.read_text()
backup=Path('/tmp/aqi-main-before-mechanics')
if not backup.exists():shutil.copytree(root,backup)
a=parse((backup/path.name).read_text());a=[t for t in a if not(isinstance(t,list) and t[0] in ['segment','via','zone'] or (isinstance(t,list) and t[0]=='gr_line' and child(t,'layer') and 'Edge.Cuts' in str(child(t,'layer'))))];path.write_text(ser(a))
b=p.LoadBoard(str(path));mm=p.FromMM
F={f.GetReference():f for f in b.GetFootprints()}
def box(f):
 r=f.GetBoundingBox(False,False);return [p.ToMM(v) for v in [r.GetLeft(),r.GetTop(),r.GetRight(),r.GetBottom()]]
def setcenter(f,x,y):
 bb=box(f);pos=f.GetPosition();f.SetPosition(p.VECTOR2I(pos.x+mm(x-(bb[0]+bb[2])/2),pos.y+mm(y-(bb[1]+bb[3])/2)))
def intersect(a,b,g=.32):return a[0]<b[2]+g and a[2]>b[0]-g and a[1]<b[3]+g and a[3]>b[1]-g
F['J2'].Flip(F['J2'].GetPosition(),False)
for ref,angle in [('J2',0),('J3',90),('J4',90),('U1',90)]:F[ref].SetOrientationDegrees(angle)
# Target coordinates are body/courtyard centres, measured from the front upper-left.
targets={'J1':(7.5,75),'J2':(23,76),'J5':(22,6),'U1':(34,19),'SW1':(8,66.25),'SW2':(22,66.25),'SW3':(36,66.25),'SW4':(3,56),'J3':(40.275,33.5),'J4':(40.275,44.6),'U8':(33.5,57),'J6':(14,35),'U9':(29,37),'U5':(10,48),'L1':(16.5,48),'U6':(8,23),'L2':(14.5,23),'U10':(8,14),'U2':(20,69),'U3':(15,57),'U4':(21,57),'U7':(21,62),'L3':(12,41),'Q3':(18,40.5),'C9':(4.5,48),'C10':(16.5,52.5),'C12':(2.5,23),'C13':(14.5,27.5),'C30':(7,41),'C31':(22,43),'C15':(17,62),'C16':(41,57),'C2':(24,16),'C3':(24,19),'C1':(24,24),'R1':(23,26),'R2':(27,27),'R3':(29,27),'R4':(31,27),'R28':(9,18),'C18':(3,14),'C19':(11,18),'R26':(6,18),'R27':(3,18),'R17':(8,52),'R18':(8,54.5),'C11':(16.5,55),'R19':(6,26.5),'R20':(6,29),'C14':(14.5,30)}
fixed=['J1','J2','J5','U1','SW1','SW2','SW3','J3','J4','U8']
priority=fixed+['SW4','U5','L1','C9','C10','R17','R18','U6','L2','C12','C13','R19','R20','C14','U10','U9','J6','U2','U3','U4','U7','L3','Q3','C30','C31','C15','C16','C2','C3','C1','R1','R2','R3','R4']
placed=[];result={};keep=[37,10,44,27]
def valid(f):
 bb=box(f);ly=f.GetLayer()
 if bb[0]<.5 or bb[1]<.5 or bb[2]>43.5 or bb[3]>79.5:return False
 if f.GetReference()!='U1' and intersect(bb,keep,0):return False
 if any(intersect(bb,r,.35) for r in [(24,50,44,51),(24,50,27,56),(24,58,27,64),(24,63,44,64)]):return False
 return not any(intersect(bb,r) for side,r in placed if side is None or side==ly)
rest=[r for r in F if r not in priority];rest.sort(key=lambda r:-(box(F[r])[2]-box(F[r])[0])*(box(F[r])[3]-box(F[r])[1]))
choices=sorted((dx*dx+dy*dy,dx*.5,dy*.5) for dx in range(-70,71) for dy in range(-70,71))
for ref in priority+rest:
 f=F[ref];bb=box(f);x,y=targets.get(ref,((bb[0]+bb[2])/2,(bb[1]+bb[3])/2))
 options=[(0,0,0)] if ref in fixed else choices
 for _,dx,dy in options:
  setcenter(f,x+dx,y+dy)
  if valid(f):break
 else:raise RuntimeError('Cannot place '+ref+' '+str(box(f)))
 placed.append((None if ref=='J1' else f.GetLayer(),box(f)))
 for pad in f.Pads():
  if pad.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH]:
   r=pad.GetBoundingBox();placed.append((None,[p.ToMM(r.GetLeft())-.3,p.ToMM(r.GetTop())-.3,p.ToMM(r.GetRight())+.3,p.ToMM(r.GetBottom())+.3]))
 pos=f.GetPosition();result[ref]={'xy':[round(p.ToMM(pos.x),4),round(p.ToMM(pos.y),4)],'rot':(180-f.GetOrientationDegrees())%360 if f.GetLayer()==p.B_Cu else f.GetOrientationDegrees(),'side':'back' if f.GetLayer()==p.B_Cu else 'front'}
 if ref in targets:print(ref, result[ref], 'shift',round(math.hypot(dx,dy),2))
for ly in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
 z=p.ZONE(b);z.SetLayer(ly);z.SetIsRuleArea(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(True);poly=z.Outline();poly.NewOutline()
 for x,y in [(37,10),(44,10),(44,27),(37,27)]:poly.Append(mm(x),mm(y))
 b.Add(z)
outline=[(1.5,0),(42.5,0),(44,1.5),(44,50),(24,50),(24,56),(27,56),(27,51),(44,51),(44,63),(27,63),(27,58),(24,58),(24,64),(44,64),(44,78.5),(42.5,80),(1.5,80),(0,78.5),(0,1.5)]
for a,c in zip(outline,outline[1:]+outline[:1]):
 sh=p.PCB_SHAPE();sh.SetShape(p.SHAPE_T_SEGMENT);sh.SetStart(p.VECTOR2I(mm(a[0]),mm(a[1])));sh.SetEnd(p.VECTOR2I(mm(c[0]),mm(c[1])));sh.SetLayer(p.Edge_Cuts);sh.SetWidth(mm(.05));b.Add(sh)
# No plane fill over the thermal neck; only explicit narrow signal/power traces.
for ly in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
 z=p.ZONE(b);z.SetLayer(ly);z.SetIsRuleArea(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False);poly=z.Outline();poly.NewOutline()
 for x,y in [(23.5,55.5),(27.5,55.5),(27.5,58.5),(23.5,58.5)]:poly.Append(mm(x),mm(y))
 b.Add(z)
d=json.loads((root/'design.json').read_text());d['keepouts']=[[[37,10],[44,10],[44,27],[37,27]]]
for c in d['components']:
 if c['ref'] in result:c.update(result[c['ref']])
(root/'design.json').write_text(json.dumps(d,indent=2));(root/'placement.json').write_text(json.dumps(result,indent=2))
p.SaveBoard(str(path),b);pro.write_text(saved)
print('Placed',len(F),'footprints; old routing removed for revision.')
