"""Collision-checked A* finishing routes for the mechanically revised main board.
Run after export_route_geometry.py; emits routes, does not modify the PCB.
"""
import json,heapq,math,time
from shapely.geometry import Point,LineString,box,Polygon
from shapely.ops import unary_union
from shapely.prepared import prep
D=json.load(open('/tmp/aqi-battery-geometry.json'));obs=D['objects'];layers=[2,0];step=.05
pads={(o['ref'],o['pin']):o for o in obs if o['type']=='pad' and o['pin']}
def geometry(o):
 if o['type']=='pad':return box(*o['box'])
 if o['type']=='via':return Point(o['xy']).buffer(o['r'])
 return LineString([o['a'],o['z']]).buffer(o['r'])
outline=Polygon(D['outline']);antenna=Polygon();via_bounds=prep(outline.buffer(-.61))
allpads=prep(unary_union([geometry(o) for o in obs if o['type']=='pad']).buffer(.19))
report=json.load(open('hardware/rev-b/battery/review/drc.json'))
plans=[]
for i,v in enumerate(report['unconnected_items']):
 items=v['items'];keys=[]
 if 'unconnected-(' in items[0]['description']:continue
 for j,it in enumerate(items):
  desc=it['description'];net=desc.split('[')[1].split(']')[0];x,y=it['pos']['x'],it['pos']['y'];key=('N',str(i)+'_'+str(j));keys.append(key)
  pads[key]={'net':net,'xy':[x,y],'layers':[2 if 'B.Cu' in desc else 0]}
 plans.append(tuple(keys))
results=[]
for src,dst in plans:
 a,z=pads[src],pads[dst];net=a['net'];assert net==z['net'],(src,dst,net,z['net'])
 width=.2 if net=='/USB_VBUS_IN' or net=='/USB_VBUS_OUT' else .15
 bounds=prep(outline.buffer(-.3001-width/2).difference(antenna.buffer(width/2+.01)))
 others=[(o,geometry(o)) for o in obs if o['net']!=net]
 blocked={l:prep(unary_union([g for o,g in others if l in o['layers']]).buffer(.1501+width/2)) for l in layers}
 vblocked=prep(unary_union([g for o,g in others]).buffer(.46))
 xy=lambda u:(round(u[0]*step,5),round(u[1]*step,5))
 point_cache={};via_cache={}
 def good(u):
  if u not in point_cache:
   pt=Point(xy(u));point_cache[u]=bounds.contains(pt) and not blocked[u[2]].intersects(pt)
  return point_cache[u]
 def segment(p,q,l):return bounds.covers(LineString([p,q])) and not blocked[l].intersects(LineString([p,q]))
 def via_good(u):
  if any(o["type"]=="via" and o["net"]==net and math.dist(xy(u),o["xy"])<.001 for o in obs):return True
  k=u[:2]
  if k not in via_cache:
   pt=Point(xy(u));via_cache[k]=via_bounds.contains(pt) and not vblocked.intersects(pt) and not allpads.intersects(pt) and all(math.dist(xy(u),o['xy'])>=.55 for o in obs if o['type']=='via')
  return via_cache[k]
 start=a['xy'];end=z['xy'];sl=next(l for l in layers if l in a['layers']);el=next(l for l in layers if l in z['layers'])
 # Board pads report all copper layers for plated-through pads, which are valid layer starts.
 costs={};parents={};queue=[]
 cx,cy=round(start[0]/step),round(start[1]/step)
 for dx in range(-7,8):
  for dy in range(-7,8):
   u=(cx+dx,cy+dy,sl);q=xy(u)
   if good(u) and segment(start,q,sl):
    g=math.dist(start,q);costs[u]=g;parents[u]=None;heapq.heappush(queue,(g+math.dist(q,end),g,u))
 done=None;t0=time.monotonic();iterations=0
 while queue:
  _,g,u=heapq.heappop(queue)
  if g!=costs[u]:continue
  iterations+=1;p=xy(u)
  if u[2]==el and math.dist(p,end)<1.0 and segment(p,end,el):done=u;break
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   v=(u[0]+dx,u[1]+dy,u[2]);q=xy(v)
   if not good(v) or not segment(p,q,u[2]):continue
   ng=g+step*math.hypot(dx,dy)
   if ng<costs.get(v,1e12):costs[v]=ng;parents[v]=u;heapq.heappush(queue,(ng+math.dist(q,end),ng,v))
  if via_good(u):
   for l in layers:
    v=(u[0],u[1],l);ng=g+3
    if l!=u[2] and good(v) and ng<costs.get(v,1e12):costs[v]=ng;parents[v]=u;heapq.heappush(queue,(ng+math.dist(p,end),ng,v))
  if iterations>350000:break
 if done is None:
  print('FAILED',net,src,dst,len(costs),flush=True);json.dump(results,open('/tmp/aqi-battery-finish.json','w'),indent=2);continue
 path=[];u=done
 while u is not None:path.append([*xy(u),u[2]]);u=parents[u]
 path.reverse();path=[[start[0],start[1],sl]]+path+[[end[0],end[1],el]]
 clean=[path[0]]
 for i in range(1,len(path)-1):
  u=clean[-1];v=path[i];w=path[i+1]
  if u[2]!=v[2] or v[2]!=w[2] or abs((v[0]-u[0])*(w[1]-v[1])-(v[1]-u[1])*(w[0]-v[0]))>1e-8:clean.append(v)
 clean.append(path[-1]);result=dict(net=net,width=width,path=clean,source=src,target=dst);results.append(result)
 for u,v in zip(clean,clean[1:]):
  if u[2]!=v[2]:obs.append(dict(type='via',net=net,layers=[0,2],xy=u[:2],r=.3))
  elif u[:2]!=v[:2]:obs.append(dict(type='track',net=net,layers=[u[2]],a=u[:2],z=v[:2],r=width/2))
 print('SOLVED',net,src,dst,'segments',len(clean)-1,'nodes',iterations,'sec',round(time.monotonic()-t0,1),flush=True)
 json.dump(results,open('/tmp/aqi-battery-finish.json','w'),indent=2)
