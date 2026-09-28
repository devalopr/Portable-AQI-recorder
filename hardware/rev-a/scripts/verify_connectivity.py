"""Compare every intended electrical pin with the exported schematic and PCB."""
from pathlib import Path
import sys,json,xml.etree.ElementTree as ET
import pcbnew as p
folder=Path(sys.argv[1]);d=json.loads((folder/'design.json').read_text());b=p.LoadBoard(str(folder/(d['name']+'.kicad_pcb')))
def normal(n):return n.lstrip('/') if n else None
netmap={}
for net in ET.parse(folder/'review/netlist.xml').findall('./nets/net'):
 for node in net.findall('node'):netmap[(node.attrib['ref'],node.attrib['pin'])]=normal(net.attrib['name'])
boardmap={(f.GetReference(),pad.GetNumber()):normal(pad.GetNetname()) for f in b.GetFootprints() for pad in f.Pads() if pad.GetNumber()}
issues=[];checked=0
for c in d['components']:
 if c['ref'].startswith('#'):continue
 for pin,expected in c['nets'].items():
  key=(c['ref'],str(pin));actual=netmap.get(key);pn=boardmap.get(key)
  if expected is not None:
   checked+=1
   if actual!=expected:issues.append(['schematic',key,expected,actual])
   if pn!=expected:issues.append(['PCB',key,expected,pn])
  elif actual and not actual.startswith('unconnected-'):issues.append(['NC unexpectedly connected',key,actual])
report=dict(board=d['name'],connected_pins_checked=checked,issues=issues)
(folder/'review/connectivity.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert not issues
