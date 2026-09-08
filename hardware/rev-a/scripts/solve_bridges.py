import json,heapq,math
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.prepared import prep
D=json.load(open('/tmp/aqi-obstacles.json'));obs=D['objects'];allpads=unary_union([box(*o['box']) for o in obs if o['type']=='pad']).buffer(.26)
def geometry(o):
 if o['type']=='pad':return box(*o['box'])
 if o['type']=='via':return Point(o['xy']).buffer(o['r'])
 return LineString([o['a'],o['z']]).buffer(o['r'])
result=[]
for net,start,end,existing in [('+3V2',[27.1125,50.6475],[32.45,55],False),('+5V_SYS',[15.74,56.8375],[17.45,55.4145],True)]:
 others=[(o,geometry(o)) for o in obs if o['net']!=net];whole=unary_union([g for o,g in others]);B=unary_union([g for o,g in others if D['B'] in o['layers']]);F=unary_union([g for o,g in others if D['F'] in o['layers']]);vc=prep(whole.buffer(.46));bc=prep(B.buffer(.235));fc=prep(F.buffer(.31));pv=prep(allpads)
 def pick(pt):
  candidates=[(round(pt[0]+dx*.1,4),round(pt[1]+dy*.1,4)) for dx in range(-30,31) for dy in range(-30,31)];candidates.sort(key=lambda q:math.dist(q,pt))
  for q in candidates:
   if not vc.intersects(Point(q)) and not pv.intersects(Point(q)) and not bc.intersects(LineString([pt,q])):return q
  raise ValueError('No via escape '+net+str(pt))
 a=pick(start);z=end if existing else pick(end);print(net,'vias',a,z)
 # Fine grid shifted to the first via. A* on front copper, testing every edge.
 step=.15;st=(0,0);target=(round((z[0]-a[0])/step),round((z[1]-a[1])/step));xy=lambda v:(a[0]+v[0]*step,a[1]+v[1]*step)
 queue=[(math.dist(a,z),0,st)];cost={st:0};parent={};done=None
 while queue:
  _,g,v=heapq.heappop(queue)
  if g!=cost[v]:continue
  p=xy(v)
  if math.dist(p,z)<.3 and not fc.intersects(LineString([p,z])):done=v;break
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   w=(v[0]+dx,v[1]+dy);q=xy(w)
   if not(.5<q[0]<43.5 and .5<q[1]<72.5) or fc.intersects(LineString([p,q])):continue
   ng=g+math.hypot(dx,dy)*step
   if ng<cost.get(w,1e9):cost[w]=ng;parent[w]=v;heapq.heappush(queue,(ng+math.dist(q,z),ng,w))
 if done is None:raise ValueError('No front route')
 path=[z,xy(done)]
 while done!=st:done=parent[done];path.append(xy(done))
 path.reverse();clean=[path[0]]
 for i in range(1,len(path)-1):
  u=clean[-1];v=path[i];w=path[i+1]
  if abs((v[0]-u[0])*(w[1]-v[1])-(v[1]-u[1])*(w[0]-v[0]))>1e-8:clean.append(v)
 clean.append(path[-1]);result.append(dict(net=net,start=start,end=end,via_a=a,via_z=None if existing else z,path=clean))
open('/tmp/aqi-bridges.json','w').write(json.dumps(result,indent=2));print('Solved',len(result),'bridges')
