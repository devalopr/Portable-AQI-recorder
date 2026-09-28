"""Rotate output headers and move inward, keeping the holder and screw clearances."""
from pathlib import Path
import shutil
from kicad_common import parse,ser,child,val,children
import pcbnew as p
R=Path(__file__).resolve().parents[1]/'integrated-power';path=R/'AQI_IP5310_Power.kicad_pcb';backup=R/'review/before-vertical-headers.kicad_pcb'
assert not backup.exists(),'Already applied'
shutil.copy2(path,backup);pro=path.with_suffix('.kicad_pro');settings=pro.read_text();raw=parse(path.read_text())
ids={'4a9dad32-510c-49e0-8934-be0e6e86b535','1db1bc10-2be2-4ecf-bc40-d068485650f2','7e7b2724-060f-4eb5-bfb5-deafc890b9d1','db95c083-1c04-4764-9bb0-0755942e3773','c9959419-2bde-4ff1-b124-05cb2a9d8fa5','b94eed17-d6a1-4aa4-a457-9435730485b9','0975ec03-32d2-4034-b226-d16f2b072d5a','0dc6f0f0-c69d-4403-a21a-be7dd021da9b','3ccfc362-a358-4d11-ba71-1405cca55a99','82c115bb-fd26-493b-bde4-186ea04af728','cad9cbfb-b9ef-4fff-a6e0-15003960181e'}
raw[:]=[a for a in raw if not(isinstance(a,list) and a[0] in ['segment','via'] and val(child(a,'uuid')[1]) in ids)];path.write_text(ser(raw));b=p.LoadBoard(str(path));mm=p.FromMM
for f in b.GetFootprints():
 if f.GetReference() in ['J8','J9']:
  f.SetOrientationDegrees(0);f.SetPosition(p.VECTOR2I(mm(5.3 if f.GetReference()=='J8' else 21.2),mm(2.5)))
def route(net,pts,layer,width):
 for a,z in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(mm(a[0]),mm(a[1])));t.SetEnd(p.VECTOR2I(mm(z[0]),mm(z[1])));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(b.FindNet(net));b.Add(t)
route('V5',[(4,8.6331),(4,3.8),(5.3,2.5)],p.F_Cu,.8)
route('V3V3',[(22.5,11),(22.5,6.34),(21.2,5.04)],p.F_Cu,.8)
route('/KEY_GATE',[(3.940048,7.496949),(3.8,7),(3.8,.8),(22.9,.8),(22.9,8.7),(25.003636,12.456757)],p.B_Cu,.15)
p.SaveBoard(str(path),b);pro.write_text(settings)
