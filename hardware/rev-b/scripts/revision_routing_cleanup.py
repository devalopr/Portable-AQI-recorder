from pathlib import Path
import pcbnew as p
from kicad_common import parse,ser,child,val
r=Path(__file__).resolve().parents[1]/'integrated-power';f=r/'AQI_IP5310_Power.kicad_pcb';pro=f.with_suffix('.kicad_pro');settings=pro.read_text();a=parse(f.read_text())
# Remove LED tails before relocating the package into free input-end space.
nets={'/LED_R','/LED_G','/LED_B','/PROT_CS'}
a[:]=[x for x in a if not(isinstance(x,list) and x[0] in ['segment','via'] and child(x,'net') and val(child(x,'net')[-1]) in nets)];f.write_text(ser(a));b=p.LoadBoard(str(f));fs={x.GetReference():x for x in b.GetFootprints()}
fs['D1'].SetPosition(p.VECTOR2I(p.FromMM(3.8),p.FromMM(84.5)))
fs['R10'].SetPosition(p.VECTOR2I(p.FromMM(23.8),p.FromMM(93.0)))
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and p.ToMM(t.GetWidth())<.15:t.SetWidth(p.FromMM(.15))
p.SaveBoard(str(f),b);pro.write_text(settings)
