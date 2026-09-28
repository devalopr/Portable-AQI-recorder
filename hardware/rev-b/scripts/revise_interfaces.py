"""Interface revision: centred USB input, dual bare headers, optional SMD NTC."""
from pathlib import Path
import json,sys
from kicad_common import Project
import pcbnew as p
r=Path(__file__).resolve().parents[1]/'battery';dp=r/'design.json';d=json.loads(dp.read_text());d['components']=[c for c in d['components'] if c['ref'] not in ['J4','TP1','TP2','TP3']];D={c['ref']:c for c in d['components']}
D['J1'].update(lib='Connector:USB_C_Receptacle',fp='Connector_USB:USB_C_Receptacle_Amphenol_12401610E4-2A',mpn='12401610E4#2A',manufacturer='Amphenol',datasheet='https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/c12401610_c.pdf',xy=[13.1,82.77],rot=180,note='USB2 data retained. Unused SuperSpeed and SBU contacts NC. Matching library STEP model; centred on 26.2mm board.')
for side in ['A','B']:
 for n in [2,3,10,11]:D['J1']['nets'][side+str(n)]=None
# Remove stale boilerplate saying that an external NTC is mandatory.
for c in d['components']:
 if c['ref']=='U1':c['note']+=' R36 supplies the normal-temperature bypass by default. Remove R36 when fitting TH1.'
D['Q2']['xy']=[21.5,82];D['U5']['xy']=[4.5,82];D['D2']['xy']=[4.5,77]
for ref,xy in [('R9',[3,74]),('C5',[4,79]),('R10',[21,76])]:D[ref]['xy']=xy
for ref,x in [('J8',3),('J9',23.2)]:
 d['components'].append(dict(ref=ref,lib='Connector_Generic:Conn_01x03',value='3V3 / 5V / GND',fp='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',nets={'1':'GEN_3V3','2':'BOOST_5V','3':'GND'},xy=[x,8],rot=0,side='back',sch=[680,570] if ref=='J8' else [775,522],dnp=True,note='Unpopulated plated holes. 2.54mm pitch. Trim soldered wire ends flush on holder side. Shared output current budget.'))
d['components'].append(dict(ref='R36',lib='Device:R_Small_US',value='10kR 1%',fp='Resistor_SMD:R_0603_1608Metric',nets={'1':'CELL_NTC','2':'GND'},xy=[4,59],rot=0,side='back',sch=[465,185],note='DEFAULT POPULATED: fixed temperature bypass. Remove when fitting TH1. Never populate both R36 and TH1.'))
d['components'].append(dict(ref='TH1',lib='Device:Thermistor_NTC',value='10kR NTC / 3435K',mpn='NTCS0603E3103FLT',manufacturer='Vishay',datasheet='https://www.vishay.com/docs/29056/ntcs0603e3t.pdf',fp='Resistor_SMD:R_0603_1608Metric',nets={'1':'CELL_NTC','2':'GND'},xy=[2,39],rot=90,side='back',sch=[525,185],dnp=True,note='Optional SMD PCB-temperature sensing; remove R36 to enable. Does not directly sense cell temperature. 0603, 10k at25C, B25/85 3435K.'))
d['blocks'][1]['title']='CHARGER / optional PCB temperature sensing'
dp.write_text(json.dumps(d,indent=2)+'\n');pp=r/(d['name']+'.kicad_pro');pro=pp.read_text();P=Project(dp);P.board();P.schematic();sp=r/(d['name']+'.kicad_sch');sp.write_text(sp.read_text().replace('(paper "A2")','(paper "A1")'));pp.write_text(pro)
