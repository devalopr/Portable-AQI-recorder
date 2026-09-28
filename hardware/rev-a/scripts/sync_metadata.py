"""Synchronize names and BOM fields without changing electrical topology or routes."""
from pathlib import Path
import sys,json,xml.etree.ElementTree as ET
import pcbnew as p
root=Path(sys.argv[1]);d=json.loads((root/'design.json').read_text());name=d['name'];path=root/(name+'.kicad_pcb');pro=root/(name+'.kicad_pro');saved=pro.read_text();b=p.LoadBoard(str(path));xml=ET.parse(root/'review/netlist.xml');cs={c.attrib['ref']:c for c in xml.findall('./components/comp')};wanted={}
for net in xml.findall('./nets/net'):
 for node in net.findall('node'):wanted[node.attrib['ref'],node.attrib['pin']]=net.attrib['name']
for f in b.GetFootprints():
 c=cs[f.GetReference()];f.SetValue(c.findtext('value') or '')
 fields={field.attrib['name']:field.text or '' for field in c.findall('./fields/field') if field.attrib['name'] not in ['Reference','Value','Footprint']}
 fields['Datasheet']=c.findtext('datasheet') or '';f.SetFields(fields)
 for key in fields:f.GetField(key).SetVisible(False)
 for pad in f.Pads():
  key=(f.GetReference(),pad.GetNumber())
  if key in wanted and pad.GetNetname()!=wanted[key]:pad.GetNet().SetNetname(wanted[key])
p.SaveBoard(str(path),b);pro.write_text(saved)
