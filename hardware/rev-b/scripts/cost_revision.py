"""Generate a separate cost-reduction schematic; never overwrite routed Rev B."""
import copy,json
from pathlib import Path
from kicad_common import Project
root=Path(__file__).resolve().parents[1]
out=root/'cost-revision'
d=json.loads((root/'battery/design.json').read_text())
d['name']='AQI_Battery_Cost_Revision'
D={c['ref']:c for c in d['components']}
def custom(name,pins):
    d['custom_symbols'].append(dict(name=name,pins=[dict(number=str(i+1),name=n,type=t,side=s) for i,(n,t,s) in enumerate(pins)]))
    return 'AQI:'+name
def resistor(ref,value,a,b,sch):
    c=copy.deepcopy(D['R3']);c.update(ref=ref,value=value,mpn='TBD',manufacturer='TBD',lcsc='',nets={'1':a,'2':b},sch=sch,xy=None,note='1% resistor; exact procurement part pending')
    d['components'].append(c);D[ref]=c
# Keep the dedicated SOC gauge and host connector as standard fitted components.
for ref in ['U4','J3']:
    D[ref]['dnp']=False
    D[ref]['note']='Required standard population: I2C battery percentage and host interconnect.'
D['U4']['lcsc']='C2682616'
# Replace the 3.3 V buck-boost with a buck downstream of the existing 5 V boost.
lib=custom('SY8089A1', [('EN','input','left'),('GND','power_in','bottom'),('LX','passive','right'),('IN','power_in','left'),('FB','input','right')])
D['U3'].update(lib=lib,value='SY8089A1 / 3.3V',mpn='SY8089A1AAC',manufacturer='Silergy',lcsc='C479074',fp='Package_TO_SOT_SMD:SOT-23-5',nets={'1':'BOOST_5V','2':'GND','3':'BUCK_3V3_SW','4':'BOOST_5V','5':'BUCK_3V3_FB'},datasheet='https://www.silergy.com/download/downloadFile?ftype=note&id=3756&type=product',note='3.3V derived from 5V. Both outputs share the boost power budget.')
D['L2']['nets']={'1':'BUCK_3V3_SW','2':'GEN_3V3'}
for ref in ['C11','C12']:D[ref]['nets']['1']='BOOST_5V'
D['C11']['sch']=[570,315]
resistor('R37','225kR','GEN_3V3','BUCK_3V3_FB',[742,315])
resistor('R38','49.9kR','BUCK_3V3_FB','GND',[785,315])
# Charge selector stays a small signal switch: no charging current in its contacts.
lib=custom('ETA6003', [('SYS','power_out','right'),('IN','power_in','left'),('SW','passive','right'),('SW','passive','right'),('PGND','power_in','bottom'),('ENB','input','left'),('NTC','input','left'),('ENPPB','input','left'),('STAT','open_collector','right'),('GND','power_in','bottom'),('ISET1','input','left'),('ISET2','input','left'),('USB_DET','input','left'),('BATT','passive','right'),('SYS','passive','right'),('BATT','passive','right'),('EP','passive','bottom')])
D['U1'].update(lib=lib,value='ETA6003 / 4.2V',mpn='ETA6003Q3Q',manufacturer='ETA Solutions',lcsc='C5455585',fp='Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.675x1.675mm',nets={str(k):v for k,v in {1:'CHG_SYS',2:'USB_VBUS_IN',3:'CHG_SW',4:'CHG_SW',5:'GND',6:'GND',7:'CELL_NTC',8:'GND',9:'CHARGE_STATUS_N',10:'GND',11:'CHG_ICHG',12:'CHG_USB_RATE',13:'INPUT_HIGH_N',14:'CELL_POS',15:'CHG_SYS',16:'CELL_POS',17:'GND'}.items()},datasheet='https://files.waveshare.com/upload/3/3f/ETA6003.pdf',note='Engineering candidate. Verify exposed-pad connection and input total-current limiting before layout release.')
remove=set('C2 C6 C16 R6 R11 R15 R16 R20 R21 R22 Q3 Q4'.split())
d['components']=[c for c in d['components'] if c['ref'] not in remove]
D['U6']['nets']['4']=None
D['R3'].update(value='2kR')
D['R4'].update(value='1kR')
D['R5'].update(value='1kR')
D['R12'].update(value='9.09kR',nets={'1':'USB_VBUS_IN','2':'CELL_NTC'})
D['SW1']['note']='Nominal 0.5/1/1.5 A on capable supply; open contact defaults to 0.5 A. Adjust with USB input disconnected.'
resistor('R39','2kR','CHG_USB_RATE','GND',[485,140])
# Separate bypass and optional NTC retained. R12 + 10k/B3435 is approximately 0-45C.
D['C1'].update(value='10uF 16V X7R',fp='Capacitor_SMD:C_0805_2012Metric')
D['R12']['sch']=[440,140]
# User approved approximate voltage-derived SOC on 2026-09-11.
# MCU reports it over the original I2C wires and drives the RGB directly.
remove=set('U9 U10 R28 R29 R30 R31 R32 C22 C23'.split())
d['components']=[c for c in d['components'] if c['ref'] not in remove]
D['U4'].update(lib='MCU_WCH_RiscV:CH32V003FxPx',value='CH32V003F4P6',mpn='CH32V003F4P6',manufacturer='WCH',lcsc='C5187096',fp='Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',datasheet='https://www.wch-ic.com/downloads/CH32V003DS0_PDF.html',nets={str(i):None for i in range(1,21)},sch=[647,430],note='Voltage-based approximate SOC, not a fuel gauge. Firmware required for I2C/LED only; charging and protection remain hardware controlled.')
D['U4']['nets'].update({'1':'RGB_R','2':'RGB_G','3':'RGB_B','4':'MCU_NRST','7':'GND','9':'GEN_3V3','10':'CHARGE_STATUS_N','11':'I2C_SDA','12':'I2C_SCL','18':'MCU_SWIO','19':'BAT_ADC','20':'VIN_ADC'})
D['D1']['nets']['2']='GEN_3V3'
for ref,net in [('R33','RGB_R'),('R34','RGB_G'),('R35','RGB_B')]:D[ref]['nets']['2']=net
D['C21']['sch']=[584,490]
resistor('R40','100kR','CELL_POS','BAT_ADC',[312,455])
resistor('R41','100kR','BAT_ADC','GND',[355,455])
resistor('R42','100kR','USB_VBUS_IN','VIN_ADC',[398,455])
resistor('R43','100kR','VIN_ADC','GND',[441,455])
resistor('R44','10kR','GEN_3V3','CHARGE_STATUS_N',[484,455])
resistor('R45','10kR','GEN_3V3','MCU_NRST',[742,455])
for ref,net,sch in [('C26','BAT_ADC',[312,490]),('C25','VIN_ADC',[398,490])]:
    c=copy.deepcopy(D['C21']);c.update(ref=ref,nets={'1':net,'2':'GND'},sch=sch,xy=None);d['components'].append(c)
for ref,net,sch in [('TP4','MCU_SWIO',[699,525]),('TP5','MCU_NRST',[742,525]),('TP6','GEN_3V3',[785,525]),('TP7','GND',[656,525])]:
    c=dict(ref=ref,lib='Connector:TestPoint',value=net,fp='TestPoint:TestPoint_Pad_D1.0mm',nets={'1':net},sch=sch,xy=None,mpn='',manufacturer='');d['components'].append(c)
# HUSB320 sink mode: pin-compatible numbering, but PORT needs a resistor.
spec=copy.deepcopy(next(s for s in d['custom_symbols'] if s['name']=='TUSB320LAI'))
spec['name']='HUSB320_BA000';d['custom_symbols'].append(spec)
D['U6'].update(lib='AQI:HUSB320_BA000',value='HUSB320 / INPUT',mpn='HUSB320-BA000-QN12R',manufacturer='Hynetek',lcsc='C7471906',datasheet='https://www.hynetek.com/uploadfiles/site/219/news/4ded9a63-401a-4cf0-a009-d45e4f8b8075.pdf',note='GPIO sink; OUT1 low for 1.5A/3A Rp. 900k PORT resistor required. Footprint dimensions require final cross-check.')
D['U6']['nets'].update({'3':'INPUT_PORT','4':'USB_VBUS_IN'})
resistor('R46','900kR','INPUT_PORT','GND',[100,140])
# Hardware total input current limiting. SY6280A has no discharge resistor.
lib=custom('SY6280A',[('OUT','power_out','right'),('GND','power_in','bottom'),('ISET','input','left'),('EN','input','left'),('IN','power_in','left')])
c=copy.deepcopy(D['U3']);c.update(ref='U11',lib=lib,value='SY6280A / input limit',mpn='SY6280AAAC',lcsc='C207620',nets={'1':'CHARGER_INPUT','2':'GND','3':'IN_LIMIT_SET','4':'USB_VBUS_IN','5':'USB_VBUS_IN'},sch=[215,85],xy=None,datasheet='https://www.silergy.com/download/downloadFile?ftype=note&id=4369&type=product',note='Nominal 0.4A / 1.18A limit, allowing for 25% tolerance. Source negotiation and total input-current budget must be bench verified.')
d['components'].append(c)
D['U1']['nets']['2']='CHARGER_INPUT'
D['R12']['nets']['1']='CHARGER_INPUT'
D['C1']['nets']['1']='CHARGER_INPUT'
resistor('R47','17kR','IN_LIMIT_SET','GND',[26,175])
resistor('R48','8.66kR','IN_LIMIT_SET','LIMIT_BRANCH',[69,175])
# Reuse the former hardware gate inverter. OUT1 high => low input limit.
src={c['ref']:c for c in json.loads((root/'battery/design.json').read_text())['components']}
for ref,sch in [('Q3',[110,85]),('Q4',[160,85]),('R20',[112,175]),('R21',[155,175]),('R22',[198,175])]:
    c=copy.deepcopy(src[ref]);c['sch']=sch;c['xy']=None
    if ref=='Q4':c['nets']['3']='LIMIT_BRANCH'
    d['components'].append(c)
# The buck output is behind a passive inductor; explicitly identify its power source.
d['components'].append(dict(ref='#FLG20',lib='power:PWR_FLAG',value='PWR_FLAG',fp='',nets={'1':'GEN_3V3'},sch=[250,566],xy=None))
# Keep USB OUT attach logic unchanged until the cheaper source controller's
# reset current advertisement has been independently verified.
d['blocks'][7]['title']='RGB / voltage-divider sensing'
d['blocks'][1]['title']='ETA6003 / power path and 4.2V charging'
d['blocks'][5]['title']='3.3V BUCK / supplied from 5V rail'
d['blocks'][8]['title']='MCU / approximate I2C SOC and programming'
d['notes']=[dict(text='COST REVISION — SCHEMATIC STUDY ONLY / NOT FOR FABRICATION',x=12,y=10,size=2.4),dict(text='CH32V003 replaces fuel gauge and analog RGB circuit. 2 layers intended. Source limiting can reduce selected charge rate.',x=12,y=20),dict(text='Charging/protection are hardware controlled. Firmware needed for approximate percentage. GPIO/ADC and current-limit qualification pending.',x=12,y=568)]
d['status']='Schematic engineering study; no replacement production PCB released'
d['output_requirement']={'5v_continuous_a': 2.0, 'external_3v3': False, 'current_scope': 'total shared across all 5 V outputs', 'internal_logic_supply_required': True, 'implemented': False}
d['notes'].append(dict(text='NEW REQUIREMENT: 1.5A at 5V and 1.5A at 3.3V. This draft power stage has NOT yet been resized or qualified for these ratings.',x=12,y=557))
# Standalone PWM telemetry: discrete MOSFET isolates the MCU from host pull-up voltage.
D['U4']['nets'].update({'11':'BAT_PWM_GATE','12':None})
D['U4']['note']='PC1 drives Q5: positive gate sinks BAT_PWM. Firmware reports 100Hz, 10-90% HIGH duty for 0-100% SOC.'
D['J3']['nets'].update({'7':'BAT_PWM','8':None})
D['J3']['note']='PWM interface revision: pin7 BAT_PWM open drain; pin8 NC. Not compatible with older I2C battery firmware.'
d['components']=[c for c in d['components'] if c['ref'] not in ['R18','R19']]
q5=copy.deepcopy(next(c for c in d['components'] if c['ref']=='Q4'))
q5.update(ref='Q5',nets={'1':'BAT_PWM_GATE','2':'GND','3':'BAT_PWM'},sch=[740,423],xy=None,mpn='2N7002',manufacturer='Nexperia',note='Open-drain PWM: external 10k pull-up to host logic rail, 3.3V or 5V; common ground required.')
d['components'].append(q5)
resistor('R49','100kR','BAT_PWM_GATE','GND',[740,500])
d['components'].append(dict(ref='TP8',lib='Connector:TestPoint',value='BAT_PWM',fp='TestPoint:TestPoint_Pad_D1.5mm',nets={'1':'BAT_PWM'},sch=[780,500],xy=None,mpn='',manufacturer=''))
d['blocks'][8]['title']='MCU / open-drain PWM SOC and programming'
d['output_requirement']={'5v_continuous_a':2.0,'external_3v3':True,'3v3_continuous_a':1.0,'current_scope':'shared boost budget; full rail maxima not simultaneous','implemented':False}
d['telemetry']={'interface':'open-drain PWM','frequency_hz':100,'high_duty_empty':0.1,'high_duty_full':0.9,'pullup':'external 10k to host 3.3V or 5V','ground_required':True,'gh_pin':7,'reserved_nc_pin':8,'mcu_pin':'PC1 / package pin11','validity':'no pulses means unavailable; host expires after 100ms','firmware':'firmware/telemetry'}
d['notes']=[n for n in d['notes'] if not n['text'].startswith('NEW REQUIREMENT:')]
d['notes'].append(dict(text='TARGET: 5V/2A and 3.3V/1A share boost capacity. Power-stage qualification pending. GH7=PWM, GH8=NC.',x=12,y=557))

# Reflow every component into its functional block; do not inherit displaced
# Rev B annotation positions from earlier mechanical edits.
groups=[
 'J1 U6 U11 Q3 Q4 D2 R7 R8 R17 R20 R21 R22 R46 R47 R48 C15',
 'U1 L3 R12 R36 R39 TH1 C1 C3 C4 C17',
 'SW1 R3 R4 R5',
 'J2 U5 Q2 R9 R10 C5',
 'U2 L1 R13 R14 C7 C8 C9 C10',
 'U3 L2 R37 R38 C11 C12 C13 C14',
 'J7 U7 U8 R23 R24 R25 R26 R27 C18 C19 C20',
 'D1 R33 R34 R35 R40 R41 R42 R43 R44 C26 C25',
 'J3 U4 J8 J9 Q5 R49 R45 C21 C24 TP4 TP5 TP6 TP7 TP8']
assigned=set()
for i,refs in enumerate(groups):
    block=d['blocks'][i];x,y=block['x'],block['y']
    cc=[c for c in d['components'] if c['ref'] in refs.split()]
    small=[c for c in cc if c['ref'].startswith(('R','C','TP','TH'))]
    big=[c for c in cc if c not in small]
    for j,c in enumerate(big):c['sch']=[x+32+(j%4)*63,y+43+(j//4)*40];assigned.add(c['ref'])
    for j,c in enumerate(small):c['sch']=[x+18+(j%6)*42,y+112+(j//6)*27];assigned.add(c['ref'])
for i,c in enumerate(c for c in d['components'] if c['ref'].startswith('#')):c['sch']=[30+i*45,580]
assert not [c['ref'] for c in d['components'] if not c['ref'].startswith('#') and c['ref'] not in assigned]
for spec in d['custom_symbols']:
    if spec['name']=='ETA6003':
        for pin in spec['pins']:
            if pin['number'] in ['5','10']:pin['side']='left'
from sync_cost_bom import annotate_design, annotate_schematic, export_bom
annotate_design(d)
(out/'design.json').write_text(json.dumps(d,indent=2)+'\n')
p=Project(out/'design.json');p.schematic()
sch=out/(d['name']+'.kicad_sch')
sch.write_text(sch.read_text().replace('(paper "A2")','(paper "A1")'))
annotate_schematic(sch, d)
export_bom(out)
print(out)
