from pathlib import Path
import json,pcbnew as p
R=Path(__file__).resolve().parents[1]/'integrated-power';path=R/'AQI_IP5310_Power.kicad_pcb';pro=path.with_suffix('.kicad_pro');s=pro.read_text();b=p.LoadBoard(str(path));mm=p.FromMM
for x,y in json.loads((R/'review/ground-stitches.json').read_text()):
 if any(isinstance(t,p.PCB_VIA) and abs(p.ToMM(t.GetPosition().x)-x)<.01 and abs(p.ToMM(t.GetPosition().y)-y)<.01 for t in b.GetTracks()):continue
 t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(mm(x),mm(y)));t.SetWidth(mm(.6));t.SetDrill(mm(.3));t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('GND'));b.Add(t)
p.SaveBoard(str(path),b);pro.write_text(s)
