import json,sys
from pathlib import Path
from kicad_common import Project
r=Path(__file__).resolve().parents[1]/'battery';path=r/'design.json';d=json.loads(path.read_text());D={c['ref']:c for c in d['components']}
for i,block in enumerate(d['blocks']):
 ox,oy=block['x'],block['y'];nx=12+(i%3)*272;ny=30+(i//3)*175
 cc=[c for c in d['components'] if not c['ref'].startswith('#') and ox<=c['sch'][0]<ox+184 and oy<=c['sch'][1]<oy+114]
 big=[c for c in cc if not c['ref'].startswith(('R','C','TP'))];small=[c for c in cc if c not in big]
 for j,c in enumerate(big):c['sch']=[nx+28+(j%4)*63,ny+40+(j//4)*45]
 for j,c in enumerate(small):c['sch']=[nx+14+(j%6)*43,ny+110+(j//6)*34]
 block.update(x=nx,y=ny,w=264,h=169)
for i,c in enumerate(c for c in d['components'] if c['ref'].startswith('#')):c['sch']=[30+i*40,566]
D['U1']['nets']['7']=None
path.write_text(json.dumps(d,indent=2)+'\n');Project(path).schematic()
p=r/(d['name']+'.kicad_sch');s=p.read_text().replace('(paper "A2")','(paper "A1")');p.write_text(s)
