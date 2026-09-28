from pathlib import Path
import pcbnew as p,json
root=Path('hardware/rev-a/main');path=root/'AQI_Main.kicad_pcb';pro=root/'AQI_Main.kicad_pro';saved=pro.read_text();b=p.LoadBoard(str(path));codes={n.GetNetname():n.GetNetCode() for n in b.GetNetsByName().values()};mm=p.FromMM
pt=lambda xy:p.VECTOR2I(mm(xy[0]),mm(xy[1]))
def tr(net,a,z,layer,width):
 t=p.PCB_TRACK(b);t.SetStart(pt(a));t.SetEnd(pt(z));t.SetNetCode(codes[net]);t.SetWidth(mm(width));t.SetLayer(layer);b.Add(t)
def via(net,a):
 v=p.PCB_VIA(b);v.SetPosition(pt(a));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetNetCode(codes[net]);v.SetLayerPair(p.F_Cu,p.B_Cu);b.Add(v)
for r in json.loads((root/'review/power-bridges.json').read_text()):
 via(r['net'],r['via_a']);tr(r['net'],r['start'],r['via_a'],p.B_Cu,.15)
 if r['via_z']:via(r['net'],r['via_z']);tr(r['net'],r['end'],r['via_z'],p.B_Cu,.15)
 for a,z in zip(r['path'],r['path'][1:]):tr(r['net'],a,z,p.F_Cu,.3)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);pro.write_text(saved)
