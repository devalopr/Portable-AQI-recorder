from pathlib import Path
import pcbnew as p
r=Path(__file__).resolve().parents[1]/'battery';path=r/'AQI_Battery_Compact.kicad_pcb';pp=path.with_suffix('.kicad_pro');pro=pp.read_text();b=p.LoadBoard(str(path));mm=p.FromMM
# Holder outline crosses new bare holes; fabrication outline remains available.
for f in b.GetFootprints():
 if f.GetReference()=='J2':
  for g in f.GraphicalItems():
   if g.GetLayer()==p.F_SilkS:g.SetLayer(p.F_Fab)
for x in [5.8,20.4]:
 for text,y in [('GND',2.92),('5V',5.46),('3V3',8)]:
  t=p.PCB_TEXT(b);t.SetText(text);t.SetPosition(p.VECTOR2I(mm(x),mm(y)));t.SetLayer(p.B_SilkS);t.SetMirrored(True);t.SetTextSize(p.VECTOR2I(mm(.8),mm(.8)));t.SetTextThickness(mm(.12));b.Add(t)
p.SaveBoard(str(path),b);pp.write_text(pro)
