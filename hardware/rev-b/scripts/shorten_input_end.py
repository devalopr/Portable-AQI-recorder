"""Shorten input end by 2 mm; rerouting and validation follow separately."""
from pathlib import Path
import pcbnew as p,shutil
from kicad_common import parse,ser,children,child,val
R=Path(__file__).resolve().parents[1]/'integrated-power';path=R/'AQI_IP5310_Power.kicad_pcb';bak=R/'review/before-96mm.kicad_pcb';assert not bak.exists();shutil.copy2(path,bak)
pro=path.with_suffix('.kicad_pro');settings=pro.read_text();b=p.LoadBoard(str(path));mm=p.FromMM
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref not in ['J1','D1','C5','SW1']:continue
 old={a.GetNumber():(a.GetPosition().x,a.GetPosition().y) for a in f.Pads() if a.GetNumber() and a.GetNumber()!='SH'}
 oldpads=[(a,a.GetPosition()) for a in f.Pads()]
 if ref=='SW1':f.SetOrientationDegrees(180);f.SetPosition(p.VECTOR2I(mm(6.3),mm(86.2)))
 else:f.SetPosition(f.GetPosition()+p.VECTOR2I(0,mm(-2)))
 for a,pos in oldpads:
  for t in b.GetTracks():
   if isinstance(t,p.PCB_VIA):continue
   if t.GetStart()==pos:t.SetStart(a.GetPosition())
   if t.GetEnd()==pos:t.SetEnd(a.GetPosition())
p.SaveBoard(str(path),b);pro.write_text(settings)
r=parse(path.read_text())
for a in r:
 if not isinstance(a,list):continue
 if a[0] in ['gr_line','gr_arc'] and val(child(a,'layer')[1])=='Edge.Cuts':
  for key in ['start','end','mid']:
   q=child(a,key)
   if q and float(q[2])>90:q[2]=str(float(q[2])-2)
 if a[0]=='zone':
  if child(a,'keepout'):
   for poly in children(a,'polygon'):
    pts=child(poly,'pts');ys=[float(q[2]) for q in pts[1:]]
    if min(ys)>90:
     for q in pts[1:]:q[2]=str(float(q[2])-2)
  else:
   for poly in children(a,'polygon'):
    for q in child(poly,'pts')[1:]:
     if float(q[2])>96:q[2]=str(float(q[2])-2)
 if a[0]=='gr_text' and val(a[1]) in ['LOW','MID','HIGH']:
  q=child(a,'at');q[1]=str({'LOW':9,'MID':6,'HIGH':3}[val(a[1])]);q[2]='89.7'
path.write_text(ser(r));print('96mm trial placement saved')
