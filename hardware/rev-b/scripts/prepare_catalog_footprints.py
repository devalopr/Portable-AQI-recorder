"""Correct imported catalog footprints against archived manufacturer drawings.
Run with KiCad Python. Raw easyeda2kicad 1.0.1 imports remain unchanged.
"""
from pathlib import Path
from kicad_common import parse,ser,child,children,val,q
ROOT=Path(__file__).resolve().parents[1]/'integrated-power'
src=ROOT/'lib/catalog-source';dst=ROOT/'lib/AQI_Power.pretty'
names=['USB-C-SMD_TYPE-C-16PIN-2MD-073','TYPE-C-SMD_TYPE-C-6P_1','SW-SMD_MSK13C02-BB','LED-SMD_4P-L1.2-W1.2_BR']
def size(p,x,y):child(p,'size')[1:]=[str(x),str(y)]
for name in names:
 f=parse((src/(name+'.kicad_mod')).read_text())
 inp=name.startswith('USB-C');out=name.startswith('TYPE-C');sw=name.startswith('SW-')
 for p in children(f,'pad'):
  n=val(p[1]);a=child(p,'at');x,y=float(a[1]),float(a[2])
  if inp:
   if n in ['A1B12','A4B9','B4A9','B1A12']:
    p[1]=q({'A1B12':'A1','A4B9':'A4','B4A9':'A9','B1A12':'A12'}[n]);size(p,.6,1.15)
   elif n in ['13','14']:
    p[1]=q('SH');size(p,1.0,2.1 if y<0 else 1.8)
    child(p,'drill')[1:]=['oval','.6',str(1.7 if y<0 else 1.4)]
    a[2]=str(-1.8 if y<0 else 2.38)
   elif not n:
    p[2]='np_thru_hole';size(p,.65,.65);child(p,'drill')[1:]=['.65']
   else:size(p,.3,1.15)
  elif out:
   if n=='7':
    p[1]=q('SH');size(p,1.0,1.8);child(p,'drill')[1:]=['oval','.6','1.4']
    a[2]=str(-1.77 if y<0 else 2.03)
   else:size(p,.8 if n in ['A12','B12'] else .7,1.0)
  elif sw:
   if not n:p[2]='np_thru_hole'
   elif n in ['5','6','7','8']:p[1]=q('')
  else:
   # Manufacturer p8: total 1.33x.92, x gap .33, y gap .35.
   a[1:3]=[str(.415 if n in ['1','2'] else -.415),str(.3175 if n in ['1','4'] else -.3175)]
   size(p,.5,.285)
 f[:]=[g for g in f if not(isinstance(g,list) and g[0].startswith('fp_') and child(g,'layer') and val(child(g,'layer')[1])=='F.CrtYd')]
 a,b=((-5.12,-3.21),(5.12,5.25)) if inp else (((-5.12,-3),(5.12,5.25)) if out else (((-5.9,-2.55),(5.9,3.1)) if sw else ((-.95,-.9),(.95,.9))))
 for start,end in [((a[0],a[1]),(b[0],a[1])),((b[0],a[1]),(b[0],b[1])),((b[0],b[1]),(a[0],b[1])),((a[0],b[1]),(a[0],a[1]))]:
  f.append(parse(f'(fp_line (start {start[0]} {start[1]}) (end {end[0]} {end[1]}) (layer F.CrtYd) (width .05))'))
 if inp or out:
  # Catalogue logos/body silk crossed solder-mask openings; retain short side marks.
  f[:]=[g for g in f if not(isinstance(g,list) and g[0] in ['fp_line','fp_circle','fp_arc'] and child(g,'layer') and val(child(g,'layer')[1])=='F.SilkS')]
  for x in [-4.75,4.75]:
   f.append(parse(f'(fp_line (start {x} -.4) (end {x} 1.1) (layer F.SilkS) (width .12))'))
 for m in children(f,'model'):
  m[1]=q('${KIPRJMOD}/lib/AQI_Power.3dshapes/'+Path(val(m[1])).stem+'.step')
 # Seating offset correction for the centered STEP shell model.
 if inp:
  for m in children(f,'model'):child(child(m,'offset'),'xyz')[1:]=['0','-1.335','1.58']
 if out:
  for m in children(f,'model'):child(child(m,'offset'),'xyz')[1:]=['0','-2.03','0']
 for t in children(f,'fp_text'):
  if t[1] in ['reference','value']:child(t,'at')[1:3]=['0',str(a[1]-.7 if t[1]=='reference' else b[1]+.7)]
 f.append(parse('(descr "Catalog import corrected against archived manufacturer drawing; see CATALOG-REVIEW.md")'))
 (dst/(name+'.kicad_mod')).write_text(ser(f)+'\n')
 print(name)
