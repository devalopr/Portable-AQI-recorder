"""Plan clearance-aware ground stitches between disconnected filled regions.
Run /tmp/aqi-ground-export.py using KiCad Python first; uses current route geometry.
"""
import json
from pathlib import Path
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1]/'integrated-power/review';j=json.loads((R/'ground-regions.json').read_text());ps=[Polygon(p['pts']).buffer(0) for p in j['polys']];par=list(range(len(ps)))
def root(i):
 while par[i]!=i:i=par[i]
 return i
def merge(i,k):par[root(i)]=root(k)
for v in j['vias']:
 a=[i for i,p in enumerate(ps) if p.intersects(Point(v).buffer(.3))]
 for i in a[1:]:merge(a[0],i)
o=json.loads((R/'route-geometry.json').read_text())['objects'];blocked=unary_union([box(*a['box']).buffer(.3) for a in o if a['type']=='pad']+[Point(a['xy']).buffer(.8) for a in o if a['type']=='via']);new=[]
for i,p in enumerate(ps):
 for k,q in enumerate(ps[:i]):
  if root(i)==root(k) or j['polys'][i]['layer']==j['polys'][k]['layer']:continue
  safe=p.buffer(-.4).intersection(q.buffer(-.4)).difference(blocked)
  if not safe.is_empty:
   a=safe.representative_point();new.append([round(a.x,4),round(a.y,4)]);merge(i,k);blocked=unary_union([blocked,a.buffer(.8)])
(R/'ground-stitches.json').write_text(json.dumps(new));print('Ground stitching candidates:',new)
