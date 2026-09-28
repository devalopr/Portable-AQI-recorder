from pathlib import Path
import pcbnew as p,json
from kicad_common import parse,ser,child,val
root=Path('hardware/rev-a/main');path=root/'AQI_Main.kicad_pcb';pro=root/'AQI_Main.kicad_pro';saved=pro.read_text();a=parse(path.read_text());bad={'276a448c-897d-42c0-aeb2-ec071d6680b3','bec9f1b3-34f6-44a3-b38e-fd2f42f44c5a','752a0d1d-d7f9-45b1-9c31-afe24614ffc2','d16ad042-b2a5-42e3-acbf-e73eca8e6440'};a=[t for t in a if not(isinstance(t,list) and t[0] in ['segment','via'] and val(child(t,'uuid')[1]) in bad)];path.write_text(ser(a));b=p.LoadBoard(str(path));net=next(n.GetNetCode() for n in b.GetNetsByName().values() if n.GetNetname()=='+3V3_CO2')
for layer in [p.F_Cu,p.B_Cu,p.In2_Cu]:
 for x in [34.2,34.9]:
  t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(x),p.FromMM(62.3)));t.SetEnd(p.VECTOR2I(p.FromMM(34.6),p.FromMM(62.3)));t.SetLayer(layer);t.SetWidth(p.FromMM(.15));t.SetNetCode(net);b.Add(t)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b);pro.write_text(saved)
