from pathlib import Path
import subprocess,json,xml.etree.ElementTree as ET
cli='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
for folder,name in [('cost-revision','AQI_Battery_Cost_Revision'),('main-pwm','AQI_Main')]:
 p=Path('hardware/rev-b')/folder;r=p/'review';f=p/(name+'.kicad_sch')
 for args in [['erc','--format','json','-o',str(r/'erc.json')],['export','netlist','--format','kicadxml','-o',str(r/'netlist.xml')],['export','svg','-o',str(r)]]:
  subprocess.run([cli,'sch']+args+[str(f)],check=True,capture_output=True)
 d=json.loads((p/'design.json').read_text());xml=ET.parse(r/'netlist.xml');nets={}
 refs=[c.attrib['ref'] for c in xml.findall('./components/comp')]
 assert len(refs)==len(set(refs))
 for n in xml.findall('./nets/net'):
  for c in n.findall('node'):nets[(c.attrib['ref'],c.attrib['pin'])]=n.attrib['name'].lstrip('/')
 errors=[]
 for c in d['components']:
  if c['ref'].startswith('#'):continue
  for pin,net in c['nets'].items():
   if net and nets.get((c['ref'],pin))!=net:errors.append((c['ref'],pin,net,nets.get((c['ref'],pin))))
 assert not errors,errors
 erc=json.loads((r/'erc.json').read_text());assert not any(s['violations'] for s in erc['sheets'])
 print(folder,': ERC zero; all intended connected pins match exported netlist')
