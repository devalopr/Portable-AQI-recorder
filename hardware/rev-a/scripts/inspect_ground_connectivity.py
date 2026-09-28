from pathlib import Path
import pcbnew as p,json
b=p.LoadBoard('hardware/rev-a/main/AQI_Main.kicad_pcb');zones=[]
def pts(c):return [[p.ToMM(c.CPoint(i).x),p.ToMM(c.CPoint(i).y)] for i in range(c.PointCount())]
for z in b.Zones():
 if z.GetIsRuleArea() or z.GetNetname()!='GND':continue
 layer=z.GetLayer();poly=z.GetFilledPolysList(layer)
 for i in range(poly.OutlineCount()):zones.append(dict(layer=layer,outer=pts(poly.COutline(i)),holes=[pts(poly.CHole(i,j)) for j in range(poly.HoleCount(i))]))
Path('/tmp/aqi-ground-polygons.json').write_text(json.dumps(zones))
print('Ground polygons',len(zones))
