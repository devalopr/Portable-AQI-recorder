"""Apply reviewed battery circuit corrections and deterministic placement targets."""
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'battery/design.json'
d=json.loads(P.read_text());cs=[c for c in d['components'] if not c['ref'].startswith('#') and c['ref'] not in ['D1','R12','R15','C6']];D={c['ref']:c for c in cs}
for c in cs:
 c['nets']={str(k):('CELL_POS' if n in ['BAT_PROT','BAT_RAW'] else n) for k,n in c['nets'].items()};c['side']='front' if c['ref']=='J2' else 'back';c['note']='';c['short_value']=True
 if c['lib']=='Device:R':c['lib']='Device:R_Small_US'
 if c['ref'].startswith('R'):c['value']=c['value'].split()[0].rstrip('R')+'R'
 if c['ref'].startswith('C'):c['value']=c['value'].split()[0]+' 16V X7R'
D['J1'].update(mpn='USB4105-GF-A',manufacturer='GCT',value='USB-C INPUT + DATA',xy=[8,85],rot=0)
D['J1']['nets'].update({k:'GND' for k in ['A1','A12','B1','B12','SH']})
D['J2'].update(mpn='BH-18650-PC',manufacturer='MPD',value='65 mm 18650 / POLARITY!',xy=[22,43],rot=270)
D['J4']['nets']['2']='GND';D['J4'].update(mpn='SM02B-GHS-TB(LF)(SN)',manufacturer='JST',value='10k CELL NTC',rot=90,xy=[40,20])
D['J3'].update(value='MAIN BOARD / GH 10',rot=270,xy=[40,70])
D['U2'].update(lib='AQI:TPS61023',mpn='TPS61023DRLR',manufacturer='Texas Instruments',value='TPS61023 / 5V',datasheet='https://www.ti.com/lit/ds/symlink/tps61023.pdf',fp='Package_TO_SOT_SMD:SOT-563',nets={'1':'BOOST_FB','2':'BOOST_EN','3':'CHG_SYS','4':'GND','5':'BOOST_SW','6':'BOOST_5V'})
D['R13']['value']='750kR 0.1%';D['R14']['value']='82.5kR 0.1%' # 0.5*(1+750/82.5) = 5.045V; tolerance remains below 5.25V
D['U3'].update(fp='Package_SON:WSON-10-1EP_2.5x2.5mm_P0.5mm_EP1.2x2mm',mpn='TPS63031DSKR',value='TPS63031 / 3.3V')
D['U3']['nets'].pop('EP',None);D['U3']['nets'].update({'5':'CHG_SYS','6':'CHG_SYS','8':'CHG_SYS','11':'GND'})
for ref in ['C11','C12']:D[ref]['nets']['1']='CHG_SYS'
D['U4']['nets'].update({'5':None,'9':'GND'});D['U4']['value']='MAX17048 / 0x36'
D['U5'].update(manufacturer='Tani',value='DW01A / PROTECTOR',note='Exact Tani thresholds; never substitute without checking voltage thresholds and delay times.')
D['U4']['fp']='Package_DFN_QFN:TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm'
D['Q2']['fp']='Package_SO:TSSOP-8_4.4x3mm_P0.65mm'
D['Q2'].update(manufacturer='Fortune Semiconductor',value='FS8205A / TSSOP-8')
D['U6']['nets'].update({'5':'GEN_3V3','12':'CHARGE_STATUS_N','13':'USB_PRESENT_STATUS'});D['U6'].update(value='MCP23008 / 0x21',mpn='MCP23008T-E/SO')
D['L1'].update(value='1uH',mpn='XAL5030-102MEC',manufacturer='Coilcraft',fp='Inductor_SMD:L_Coilcraft_XAL5030-XXX',datasheet='https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xal/xal50xx/xal5030-102/')
D['L2'].update(value='2.2uH',mpn='XAL4020-222MEC',manufacturer='Coilcraft',fp='Inductor_SMD:L_Coilcraft_XAL4020-XXX',datasheet='https://www.coilcraft.com/en-us/products/power/high-voltage-inductors/xal/xal40xx/xal4020-222/')
for ref in ['R18','R19']:D[ref].update(dnp=True,note='Populate only for independent I2C operation. Main PCB supplies the pullups.')
D['R7']['value']='100kR';D['R8']['value']='150kR' # hostpresent3V nominal, main100k lowers to1.875V. Root change mainpulldown to1M for 2.8V.
D['R11']['value']='100kR'
def add(ref,lib,value,nets,fp,xy,**kw):
 c=dict(ref=ref,lib=lib,value=value,nets={str(k):v for k,v in nets.items()},fp=fp,xy=xy,sch=[20,20],side='back',rot=0,dnp=False,**kw)
 if ref in D:cs.remove(D[ref])
 cs.append(c);D[ref]=c
R='Resistor_SMD:R_0603_1608Metric';C='Capacitor_SMD:C_0603_1608Metric'
add('SW1','Switch:SW_SPDT','5V OUTPUT ENABLE',{1:'CHG_SYS',2:'BOOST_EN',3:'GND'},'Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN',[3,70],rot_unused=0,mpn='JS102011SAQN',manufacturer='C&K');D['SW1']['rot']=270
for ref,net,xy in [('R20','CHARGE_STATUS_N',[27,63]),('R21','USB_PRESENT_STATUS',[27,66])]:add(ref,'Device:R_Small_US','10kR',{1:'GEN_3V3',2:net},R,xy)
add('C15','Device:C','100nF 16V X7R',{1:'GEN_3V3',2:'GND'},C,[26,59])
add('D2','Power_Protection:USBLC6-2SC6','USBLC6-2SC6',{1:'USB_D+',6:'USB_D+',3:'USB_D-',4:'USB_D-',2:'GND',5:'USB_VBUS_IN'},'Package_TO_SOT_SMD:SOT-23-6',[12,77],mpn='USBLC6-2SC6',manufacturer='STMicroelectronics')
for ref,net,xy in [('J5','BOOST_5V',[4,12]),('J6','GEN_3V3',[4,28])]:add(ref,'Connector_Generic:Conn_01x02',('5V / 0.5A' if ref=='J5' else '3V3 / 0.3A'),{1:net,2:'GND'},'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',xy,mpn='Pin header 1x2 P2.54',manufacturer='Generic')
for i,net in enumerate(['CELL_NEG','USB_VBUS_IN','GND','PROT_VCC'],1):
 add('#FLG'+str(i),'power:PWR_FLAG','PWR_FLAG',{1:net},'',None)
# Schematic grid: generous spacing before direct-wire visual refinement.
for i,c in enumerate(cs):c['sch']=[42+(i%8)*70,40+(i//8)*46]
# Circuit clusters on the rear, holder only on the front.
positions={'U1':[17,60],'U2':[29,43],'L1':[34,43],'U3':[18,27],'L2':[23,27],'U4':[12,16],'U5':[13,8],'Q2':[20,8],'U6':[30,64], 'R3':[13,58],'R4':[13,61],'R5':[13,64],'R6':[17,66],'R9':[8,8],'R10':[17,12],'C5':[10,11],'C2':[22,58],'C3':[22,62],'C4':[12,20],'R11':[25,39],'R13':[25,46],'R14':[25,49],'C7':[24,42],'C8':[35,49],'C9':[38,49],'C10':[32,49],'C11':[13,27],'C12':[13,30],'C13':[23,33],'C14':[27,33],'R16':[18,70],'R17':[21,70],'R18':[32,73],'R19':[35,73],'R1':[5,77],'R2':[8,77],'C1':[11,70],'R7':[16,75],'R8':[19,75]}
for ref,xy in positions.items():D[ref]['xy']=xy
custom=[s for s in d['custom_symbols'] if s['name'] not in ['TPS61236P','TPS61023']]
for s in custom:
 if s['name']=='MAX17048' and not any(str(p['number'])=='9' for p in s['pins']):s['pins'].append(dict(number='9',name='EP',type='power_in',side='bottom'))
custom.append({'name':'TPS61023','pins':[dict(number=str(n),name=name,type=typ,side=side) for n,name,typ,side in [(1,'FB','input','left'),(2,'EN','input','left'),(3,'VIN','power_in','left'),(4,'GND','power_in','bottom'),(5,'SW','passive','right'),(6,'VOUT','power_out','right')]]})
d.update(components=cs,custom_symbols=custom,blocks=[],notes=[{'text':'AQI BATTERY REV A / ENGINEERING - NOT RELEASED','x':12,'y':12,'size':2.4},{'text':'Standard 65mm cell. Check polarity. Cell NTC required. USB100 default; firmware selects higher input limit only after source qualification.','x':12,'y':20}],board_texts=[{'text':'AQI POWER A','xy':[22,84],'layer':'B_SilkS'},{'text':'65mm 18650 / CHECK + -','xy':[22,42]},{'text':'CELL +','xy':[22,3]},{'text':'CELL -','xy':[22,82]}])
P.write_text(json.dumps(d,indent=2));print(len(cs),'battery schematic components')
