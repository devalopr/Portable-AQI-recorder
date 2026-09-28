"""Tighten official battery-generator courtyard around body and terminal lands."""
from pathlib import Path
from kicad_common import parse,ser,child,val
root=Path(__file__).resolve().parents[1]/'integrated-power/lib'
name='BatteryHolder_Generic_18650_77.5x21.5_Provisional.kicad_mod'
f=parse((root/'catalog-source'/name).read_text())
f[:]=[g for g in f if not(isinstance(g,list) and (g[0]=='model' or (g[0].startswith('fp_') and child(g,'layer') and val(child(g,'layer')[1])=='F.CrtYd')))]
# 0.25 mm courtyard around body and each assumed solder land.
pts=[(-44.15,-3.7),(-39,-3.7),(-39,-11),(39,-11),(39,-3.7),(44.15,-3.7),(44.15,3.7),(39,3.7),(39,11),(-39,11),(-39,3.7),(-44.15,3.7)]
for a,b in zip(pts,pts[1:]+pts[:1]):f.append(parse(f'(fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width .05) (type default)) (layer "F.CrtYd"))'))
(root/'AQI_Power.pretty'/name).write_text(ser(f)+'\n')
