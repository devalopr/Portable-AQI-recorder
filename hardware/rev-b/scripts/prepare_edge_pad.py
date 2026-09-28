"""Derive bare hand-solder pad from official KiCad test point: 0.25mm courtyard, no silk box."""
from pathlib import Path
from kicad_common import parse,ser,child,children,val,q,K
R=Path(__file__).resolve().parents[1]/'integrated-power/lib/AQI_Power.pretty'
f=parse((K/'footprints/TestPoint.pretty/TestPoint_Pad_1.5x1.5mm.kicad_mod').read_text());f[1]=q('SolderPad_1.5mm_Edge')
f[:]=[a for a in f if not(isinstance(a,list) and a[0].startswith('fp_') and child(a,'layer') and val(child(a,'layer')[1]) in ['F.CrtYd','F.SilkS'])]
for a,b in [((-1,-1),(1,-1)),((1,-1),(1,1)),((1,1),(-1,1)),((-1,1),(-1,-1))]:f.append(parse(f'(fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width .05) (type default)) (layer "F.CrtYd"))'))
(R/'SolderPad_1.5mm_Edge.kicad_mod').write_text(ser(f)+'\n')
