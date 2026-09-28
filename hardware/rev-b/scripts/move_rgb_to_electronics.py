from pathlib import Path
from kicad_common import parse,ser,child,val
import json,shutil,math
import wx
app=wx.App(False)
import pcbnew as p
root=Path(__file__).resolve().parents[1]
r=root/'battery';dp=r/'design.json';d=json.loads(dp.read_text());path=r/(d['name']+'.kicad_pcb');backup=r/'review/before-rgb-electronics';backup.mkdir(exist_ok=True)
for f in [path,dp]:
 if not (backup/f.name).exists():shutil.copy2(f,backup/f.name)
b=p.LoadBoard(str(path));f=next(f for f in b.GetFootprints() if f.GetReference()=='D1');old=[a.GetBoundingBox() for a in f.Pads()]
# Remove only traces for the moved RGB and traces touching its previous pads.
remove=set()
for t in b.GetTracks():
 pts=[t.GetPosition()] if isinstance(t,p.PCB_VIA) else [t.GetStart(),t.GetEnd()]
 if t.GetNetname().lstrip('/') in ['LED_RED','LED_GREEN','LED_BLUE'] or any(bb.Contains(v) for bb in old for v in pts):remove.add(t.m_Uuid.AsString())
raw=parse(path.read_text());raw[:]=[x for x in raw if not(isinstance(x,list) and x[0] in ['segment','via'] and val(child(x,'uuid')[1]) in remove)]
path.write_text(ser(raw));b=p.LoadBoard(str(path));f=next(f for f in b.GetFootprints() if f.GetReference()=='D1')
if f.GetLayer()!=p.B_Cu:f.Flip(f.GetPosition(),False)
f.SetOrientationDegrees(0)
def bb(fp):
 a=fp.GetBoundingBox(False,False);return [p.ToMM(a.GetLeft()),p.ToMM(a.GetTop()),p.ToMM(a.GetRight()),p.ToMM(a.GetBottom())]
def overlap(a,z):return a[0]<z[2]+.2 and a[2]>z[0]-.2 and a[1]<z[3]+.2 and a[3]>z[1]-.2
occupied=[bb(x) for x in b.GetFootprints() if x.GetLayer()==p.B_Cu and x.GetReference()!='D1']
for _,x,y in sorted(((x-4)**2+(y-83)**2,x,y) for x in [i*.5 for i in range(3,48)] for y in [i*.5 for i in range(142,172)]):
 f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));a=bb(f)
 if a[0]>.5 and a[2]<25.5 and a[1]>1 and a[3]<86.5 and not any(overlap(a,z) for z in occupied):break
else:raise RuntimeError('No collision-free LED position near input')
for c in d['components']:
 if c['ref']=='D1':c.update(side='back',xy=[x,y],rot=0)
f.Reference().SetVisible(False)
p.SaveBoard(str(path),b);dp.write_text(json.dumps(d,indent=2)+'\n')
print('RGB D1 moved to B.Cu at',x,y,'mm; affected routes require completion')
