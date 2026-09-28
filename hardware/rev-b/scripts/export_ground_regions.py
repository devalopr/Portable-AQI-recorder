"""Export actual filled ground polygons and vias for stitch planning."""
from pathlib import Path
import json
from kicad_common import parse,children,child,val
R=Path(__file__).resolve().parents[1]/'integrated-power';a=parse((R/'AQI_IP5310_Power.kicad_pcb').read_text());ps=[];vs=[]
for z in children(a,'zone'):
 if not child(z,'net') or val(child(z,'net')[-1])!='GND':continue
 for f in children(z,'filled_polygon'):ps.append(dict(layer=val(child(f,'layer')[1]),pts=[[float(x[1]),float(x[2])] for x in children(child(f,'pts'),'xy')]))
for v in children(a,'via'):
 if val(child(v,'net')[-1])=='GND':vs.append([float(x) for x in child(v,'at')[1:3]])
(R/'review/ground-regions.json').write_text(json.dumps(dict(polys=ps,vias=vs)));print('Ground polygons/vias:',len(ps),len(vs))
