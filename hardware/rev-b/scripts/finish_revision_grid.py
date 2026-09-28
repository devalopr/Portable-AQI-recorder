"""Local finishing router with rasterized clearance masks; validate results in KiCad."""
import json,heapq,math,time
from pathlib import Path
import numpy as np
from shapely.geometry import Point,LineString,box,Polygon
from shapely.ops import unary_union
from shapely import contains_xy
R=Path(__file__).resolve().parents[1]/'integrated-power/review'
D=json.loads((R/'route-geometry.json').read_text());obs=D['objects'];step=.05
nx,ny=531,1881
X,Y=np.meshgrid(np.arange(nx)*step,np.arange(ny)*step)
outline=Polygon(D['outline'])
def geom(o):
 if o['type']=='pad':return box(*o['box'])
 if o['type']=='via':return Point(o['xy']).buffer(o['r'])
 return LineString([o['a'],o['z']]).buffer(o['r'])
allpads=unary_union([geom(o) for o in obs if o['type']=='pad' and o.get('ref') not in ['TP9','TP10','TP11','TP12','TP13','TP14']]).buffer(.19)
basevia=contains_xy(outline.buffer(-.61),X,Y)&~contains_xy(allpads,X,Y)
report=json.loads((R/'routing-drc.json').read_text());plans=[]
for v in report['unconnected_items']:
 its=v['items'];desc=its[0]['description'];net=desc.split('[')[1].split(']')[0]
 if net=='GND' or net.startswith('unconnected-'):continue
 ends=[]
 for it in its:
  pos=[it['pos']['x'],it['pos']['y']];ds=it['description'];ls=[0,1] if 'Via ' in ds or 'PTH ' in ds else [0 if 'B.Cu' in ds else 1]
  ends.append((pos,ls))
 plans.append((net,*ends))
# Small local nets first, long USB pair last.
priority={'/LED_B':0,'/HOST_USB_D+':1,'/USB_D+':2,'/CC2_IN':3,'/HOST_USB_D-':4,'VLOG':9}
plans.sort(key=lambda a: (priority.get(a[0],5), math.dist(a[1][0],a[2][0])))
results=[]
for net,(start,sls),(end,els) in plans:
 t0=time.monotonic();w=.6 if net=='/USB_OUT' else (.2 if net in ['/BNEG','/PROT_VCC'] else .15)
 bound=outline.buffer(-.3001-w/2)
 other=[(o,geom(o)) for o in obs if o['net']!=net]
 blocks=[unary_union([g for o,g in other if l in o['layers']]).buffer(.1501+w/2) for l in [2,0]]
 allowed=np.array([contains_xy(bound,X,Y)&~contains_xy(b,X,Y) for b in blocks])
 vb=unary_union([g for o,g in other]).buffer(.4601)
 via=basevia&~contains_xy(vb,X,Y)
 # Existing same-net vias can be used without adding a new hole.
 for o in obs:
  if o['type']=='via' and o['net']==net:
   ix,iy=[round(v/step) for v in o['xy']]
   if abs(ix*step-o['xy'][0])<1e-5 and abs(iy*step-o['xy'][1])<1e-5:via[iy,ix]=True
 def seg(a,b,l):
  line=LineString([a,b]);return bound.covers(line) and not blocks[l].intersects(line)
 goals={};ex,ey=[round(v/step) for v in end]
 for l in els:
  for y in range(max(0,ey-10),min(ny,ey+11)):
   for x in range(max(0,ex-10),min(nx,ex+11)):
    if allowed[l,y,x] and seg([x*step,y*step],end,l):goals[l,y,x]=True
 costs={};parents={};q=[];sx,sy=[round(v/step) for v in start]
 for l in sls:
  for y in range(max(0,sy-10),min(ny,sy+11)):
   for x in range(max(0,sx-10),min(nx,sx+11)):
    if allowed[l,y,x] and seg(start,[x*step,y*step],l):
     key=(l,y,x);g=math.hypot(x*step-start[0],y*step-start[1]);costs[key]=g;parents[key]=None;heapq.heappush(q,(g+1.35*math.hypot(x*step-end[0],y*step-end[1]),g,key))
 done=None;iterations=0
 while q:
  _,g,u=heapq.heappop(q)
  if g!=costs[u]:continue
  iterations+=1
  if u in goals:done=u;break
  l,y,x=u
  candidates=[]
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
   xx,yy=x+dx,y+dy
   if 0<=xx<nx and 0<=yy<ny and allowed[l,yy,xx] and (not dx or not dy or (allowed[l,y,xx] and allowed[l,yy,x])):candidates.append(((l,yy,xx),step*math.hypot(dx,dy)))
  if via[y,x] and allowed[1-l,y,x]:candidates.append(((1-l,y,x),3.0))
  for v,d in candidates:
   ng=g+d
   if ng<costs.get(v,1e20):
    costs[v]=ng;parents[v]=u;heapq.heappush(q,(ng+1.35*math.hypot(v[2]*step-end[0],v[1]*step-end[1]),ng,v))
  if iterations>1200000:break
 if done is None:print('FAILED',net,'nodes',iterations,'starts',len(costs),'goals',len(goals),flush=True);continue
 path=[];u=done
 while u is not None:path.append([round(u[2]*step,5),round(u[1]*step,5),[2,0][u[0]]]);u=parents[u]
 path.reverse();path=[[*start,path[0][2]]]+path+[[*end,path[-1][2]]];clean=[path[0]]
 for i in range(1,len(path)-1):
  a,b,c=clean[-1],path[i],path[i+1]
  if a[2]!=b[2] or b[2]!=c[2] or abs((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))>1e-8:clean.append(b)
 clean.append(path[-1])
 # Exact geometry verification protects against raster corner crossings.
 assert all(a[2]!=b[2] or a[:2]==b[:2] or seg(a[:2],b[:2],0 if a[2]==2 else 1) for a,b in zip(clean,clean[1:])),net
 results.append(dict(net=net,width=w,path=clean))
 for a,b in zip(clean,clean[1:]):
  if a[2]!=b[2]:obs.append(dict(type='via',net=net,layers=[0,2],xy=a[:2],r=.3))
  elif a[:2]!=b[:2]:obs.append(dict(type='track',net=net,layers=[a[2]],a=a[:2],z=b[:2],r=w/2))
 (R/'finish-routes.json').write_text(json.dumps(results,indent=2))
 print('SOLVED',net,len(clean),'nodes',iterations,'sec',round(time.monotonic()-t0,1),flush=True)
