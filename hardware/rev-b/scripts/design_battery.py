"""Standalone compact battery design; regenerate only the Rev B working project."""
import json,copy
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'battery'
old=json.loads((root.parent/'rev-a/battery/design.json').read_text())
keep='J1 J2 J3 J4 U2 U3 U4 U5 Q2 L1 L2 R7 R8 R9 R10 R13 R14 C5 C7 C8 C9 C10 C11 C12 C13 C14 R18 R19 D2'.split()
cs=[copy.deepcopy(c) for c in old['components'] if c['ref'] in keep]
D={c['ref']:c for c in cs}; specs=copy.deepcopy(old['custom_symbols'])
def put(ref,lib,value,fp,nets,xy,mpn='',manufacturer='',rot=0,side='back',**kwargs):
 c=dict(ref=ref,lib=lib,value=value,fp=fp,nets={str(k):v for k,v in nets.items()},xy=list(xy),sch=[0,0],mpn=mpn,manufacturer=manufacturer,rot=rot,side=side,**kwargs);cs.append(c);D[ref]=c;return c
def custom(name,pins):
 specs.append(dict(name=name,pins=[dict(number=str(i+1),name=v.split(':')[0],type=v.split(':')[1] if ':' in v else 'passive',side=('left' if i<len(pins)/2 else 'right')) for i,v in enumerate(pins)]));return 'AQI:'+name
RFP='Resistor_SMD:R_0603_1608Metric';CFP='Capacitor_SMD:C_0603_1608Metric'
def R(ref,v,a,b,xy):return put(ref,'Device:R_Small_US',v,RFP,{1:a,2:b},xy,note='1% unless explicitly stated')
def C(ref,v,a,b,xy,big=False):return put(ref,'Device:C',v,'Capacitor_SMD:C_0805_2012Metric' if big else CFP,{1:a,2:b},xy,note='X7R; verify effective capacitance at operating bias')
D['J1'].update(fp='Connector_USB:USB_C_Receptacle_GCT_USB4110',mpn='USB4110-GF-A',xy=[5.7,83.29],rot=180,datasheet='https://gct.co/files/drawings/usb4110.pdf')
D['J2'].update(fp='Battery:BatteryHolder_Keystone_1042_1x18650',mpn='1042',manufacturer='Keystone',xy=[12.85,44],rot=90,value='18650 / Keystone 1042',datasheet='https://www.keyelco.com/product-pdf.cfm?p=918')
D['J3'].update(xy=[21.975,21],rot=-90,note='Optional AQI link. Standalone charging and outputs do not require this connector.')
D['J4'].update(xy=[3.725,59],rot=90,note='Required 10k 103AT-2 NTC in thermal contact with cell. Missing sensor inhibits charging.')
D['U2']['nets']['2']='CHG_SYS'
D['U4']['note']='Optional I2C fuel gauge for host; no host needed for charging or indicator.'
# Custom pin maps come from the saved manufacturer PDFs. BQ25606 uses RGE0024H.
u=custom('BQ25606',['VAC:power_in','NC:no_connect','D+:bidirectional','D-:bidirectional','STAT:open_collector','OTG:input','PG:open_collector','ILIM:input','CE_N:input','ICHG:input','TS:input','VSET:input','BAT:passive','BAT:passive','SYS:power_out','SYS:passive','GND:power_in','GND:power_in','SW:passive','SW:passive','BTST:passive','REGN:power_out','PMID:passive','VBUS:power_in','EP:power_in'])
put('U1',u,'BQ25606 / 4.2V','Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias',{1:'USB_VBUS_IN',2:None,3:None,4:None,5:'CHARGE_STATUS_N',6:'GND',7:'PG_N',8:'CHG_ILIM',9:'GND',10:'CHG_ICHG',11:'CELL_NTC',12:None,13:'CELL_POS',14:'CELL_POS',15:'CHG_SYS',16:'CHG_SYS',17:'GND',18:'GND',19:'CHG_SW',20:'CHG_SW',21:'CHG_BTST',22:'CHG_REGN',23:'CHG_PMID',24:'USB_VBUS_IN',25:'GND'},[12,67],'BQ25606RGER','Texas Instruments',datasheet='https://www.ti.com/lit/ds/symlink/bq25606.pdf',lcsc='C374063',note='VSET must FLOAT for 4.2V. D+/D- float so ILIM controls unknown-adapter input limit; GH USB data remain separate.')
put('L3','Device:L','2.2uH','Inductor_SMD:L_Coilcraft_XAL4020-XXX',{1:'CHG_SW',2:'CHG_SYS'},[12,60],'XAL4020-222MEC','Coilcraft')
C('C1','1uF 16V','USB_VBUS_IN','GND',[12,73]);C('C2','10uF 16V','CHG_PMID','GND',[16,70],True);C('C3','22uF 16V','CHG_SYS','GND',[17,60],True);C('C4','22uF 16V','CELL_POS','GND',[8,66],True)
C('C6','4.7uF 10V','CHG_REGN','GND',[17,67]);C('C16','47nF 16V','CHG_BTST','CHG_SW',[15,63]);C('C17','22uF 16V','CHG_SYS','GND',[19,61],True)
R('R3','1.37kR','CHG_ICHG','GND',[16,56]);R('R4','681R','CHG_ICHG','RATE_HIGH',[19,55]);R('R5','681R','RATE_HIGH','RATE_MED',[19,53])
u=custom('PCM13SMTR',['LOW:passive','MED:passive','COMMON:passive','HIGH:passive'])
put('SW1',u,'500mA / 1A / 1.5A','Button_Switch_SMD:SW_SP3T_PCM13',{1:None,2:'RATE_MED',3:'GND',4:'RATE_HIGH'},[22,49],'PCM13SMTR','C&K',rot=-90,datasheet='https://www.ckswitches.com/media/1424/pcm.pdf',note='Recessed actuator. Pin3 common. Ladder limits overlapping contacts to HIGH; open contact falls back LOW. Adjust with input power disconnected.')
R('R6','953R','CHG_ILIM','GND',[9,72]);R('R11','523R','CHG_ILIM','ILIM_BRANCH',[17,74]);R('R12','5.23kR','CHG_REGN','CELL_NTC',[8,62]);R('R15','30.9kR','CELL_NTC','GND',[6,63])
# CC controllers in GPIO mode. OUT1 pulls low for 1.5/3A sources; cap both at approx1.42A.
u=custom('TUSB320LAI',['CC1:bidirectional','CC2:bidirectional','PORT:input','VBUS_DET:input','ADDR:input','OUT3:open_collector','OUT1:open_collector','OUT2:open_collector','ID_N:open_collector','GND:power_in','EN_N:input','VDD:power_in'])
fp='Package_DFN_QFN:Texas_X2QFN-12_1.6x1.6mm_P0.4mm'
put('U6',u,'USB-C INPUT detect',fp,{1:'USB_CC1',2:'USB_CC2',3:'GND',4:'INPUT_VDET',5:None,6:None,7:'INPUT_HIGH_N',8:None,9:None,10:'GND',11:'GND',12:'USB_VBUS_IN'},[18,78],'TUSB320LAIRWBR','Texas Instruments',datasheet='https://www.ti.com/lit/ds/symlink/tusb320lai.pdf')
R('R16','887kR','USB_VBUS_IN','INPUT_VDET',[21,78]);R('R17','10kR','USB_VBUS_IN','INPUT_HIGH_N',[21,74]);C('C15','100nF 16V','USB_VBUS_IN','GND',[18,80])
# Non-failsafe OUT1 pulled only to its own VDD. Gate defaults low while its supply is absent.
put('Q3','Transistor_BJT:MMBT3904','MMBT3904','Package_TO_SOT_SMD:SOT-23',{1:'CC_BASE',2:'GND',3:'CC_GATE'},[21,69],'MMBT3904','onsemi')
R('R20','100kR','INPUT_HIGH_N','CC_BASE',[22,72]);R('R21','100kR','USB_VBUS_IN','CC_GATE',[23,66]);R('R22','1MR','CC_GATE','GND',[21,64])
put('Q4','Transistor_FET:2N7002','2N7002','Package_TO_SOT_SMD:SOT-23',{1:'CC_GATE',2:'GND',3:'ILIM_BRANCH'},[20,67],'2N7002','Nexperia')
put('J7','Connector:USB_C_Receptacle_PowerOnly_6P','5V USB-C OUTPUT','Connector_USB:USB_C_Receptacle_GCT_USB4135-GF-A_6P_TopMnt_Horizontal',{'A1':'GND','A4':'USB_VBUS_OUT','A5':'OUT_CC1','B1':'GND','B4':'USB_VBUS_OUT','B5':'OUT_CC2','SH':'GND'},[12.85,4.5],'USB4135-GF-A','GCT')
put('U7',u,'USB-C OUTPUT attach',fp,{1:'OUT_CC1',2:'OUT_CC2',3:'SOURCE_MODE',4:'OUTPUT_VDET',5:None,6:None,7:None,8:None,9:'OUT_ATTACH_N',10:'GND',11:'GND',12:'GEN_3V3'},[8,10],'TUSB320LAIRWBR','Texas Instruments',datasheet='https://www.ti.com/lit/ds/symlink/tusb320lai.pdf')
R('R23','100kR','GEN_3V3','SOURCE_MODE',[6,10]);R('R24','887kR','USB_VBUS_OUT','OUTPUT_VDET',[8,7]);R('R25','10kR','GEN_3V3','OUT_ATTACH_N',[9,12]);C('C18','100nF 16V','GEN_3V3','GND',[6,12])
u=custom('TPS2552DBV',['IN:power_in','GND:power_in','EN_N:input','FAULT_N:open_collector','ILIM:input','OUT:power_out'])
put('U8',u,'USB OUT protection','Package_TO_SOT_SMD:SOT-23-6',{1:'BOOST_5V',2:'GND',3:'OUT_ATTACH_N',4:None,5:'OUT_ILIM',6:'USB_VBUS_OUT'},[16,10],'TPS2552DBVR','Texas Instruments',datasheet='https://www.ti.com/lit/ds/symlink/tps2552.pdf')
R('R26','47.5kR','OUT_ILIM','GND',[17,13]);R('R27','10kR','USB_VBUS_OUT','GND',[19,9]);C('C19','22uF 16V','USB_VBUS_OUT','GND',[12,9],True);C('C20','100nF 16V','BOOST_5V','GND',[15,13])
# Single dim RGB. Autonomous voltage bands; blue adds a charging indication.
u=custom('LMV393_DUAL',['OUT_R:open_collector','IN_R-:input','IN_R+:input','GND:power_in','IN_G+:input','IN_G-:input','OUT_G:open_collector','VCC:power_in'])
put('U9',u,'Battery voltage bands','Package_SO:VSSOP-8_3x3mm_P0.65mm',{1:'RED_SINK',2:'VREF_1V24',3:'VBAT_HIGH_DIV',4:'GND',5:'VREF_1V24',6:'VBAT_LOW_DIV',7:'GREEN_SINK',8:'GEN_3V3'},[10,42],'LMV393IPWR','Texas Instruments',datasheet='https://www.ti.com/lit/ds/symlink/lmv393.pdf')
# LMV393IPWR is TSSOP8, use package corresponding to PW rather than VSSOP DGK.
D['U9']['fp']='Package_SO:TSSOP-8_3x3mm_P0.65mm'
u=custom('TLV431_DBZ',['REF:input','K:passive','A:passive'])
put('U10',u,'1.24V reference','Package_TO_SOT_SMD:SOT-23',{1:'VREF_1V24',2:'VREF_1V24',3:'GND'},[15,42],'TLV431BIDBZR','Texas Instruments',datasheet='https://www.ti.com/lit/ds/symlink/tlv431.pdf')
R('R28','10kR','GEN_3V3','VREF_1V24',[15,39]);R('R29','215kR','CELL_POS','VBAT_HIGH_DIV',[6,39]);R('R30','100kR','VBAT_HIGH_DIV','GND',[6,41]);R('R31','182kR','CELL_POS','VBAT_LOW_DIV',[6,43]);R('R32','100kR','VBAT_LOW_DIV','GND',[6,45]);C('C21','100nF 16V','GEN_3V3','GND',[12,45]);C('C22','100nF 16V','VBAT_HIGH_DIV','GND',[4,40]);C('C23','100nF 16V','VBAT_LOW_DIV','GND',[4,44])
u=custom('RGB_LUMEX',['B_K:passive','A:passive','R_K:passive','G_K:passive'])
put('D1',u,'Dim RGB','LED_SMD:LED_RGB_Lumex_SML-LXT0805SIUGUBW',{1:'LED_BLUE',2:'BOOST_5V',3:'LED_RED',4:'LED_GREEN'},[1.2,44],'SML-LXT0805SIUGUBW','Lumex',rot=90,side='front',datasheet='https://www.lumex.com/datasheet/files/SML-LXT0805SIUGUBW.pdf')
R('R33','10kR','LED_RED','RED_SINK',[8,47]);R('R34','10kR','LED_GREEN','GREEN_SINK',[11,47]);R('R35','10kR','LED_BLUE','CHARGE_STATUS_N',[14,47])
# Solder pads, no populated output headers.
for ref,net,y in [('TP1','BOOST_5V',49),('TP2','GEN_3V3',53),('TP3','GND',57)]:
 put(ref,'Connector:TestPoint',net,'TestPoint:TestPoint_Pad_D2.0mm',{1:net},[2,y])
# Cluster existing conversion and protection parts around preferred locations.
positions={'U2':[12,29],'L1':[12,24],'R13':[8,31],'R14':[8,33],'C7':[8,28],'C8':[16,28],'C9':[16,31],'C10':[19,31],'U3':[12,19],'L2':[12,14],'C11':[8,18],'C12':[8,20],'C13':[16,17],'C14':[16,20],'U4':[17,37],'U5':[12,76],'Q2':[12,81],'R9':[9,75],'R10':[15,77],'C5':[10,78],'R7':[5,74],'R8':[5,72],'R18':[18,39],'R19':[20,39],'D2':[8,78]}
for ref,xy in positions.items():D[ref]['xy']=xy
# Footprint angles below are the final physical angles; common builder is patched accordingly.
for c in cs:
 c.pop('direct_pins',None);c.pop('uuid',None)
 if c['ref'] not in ['J1','J2','J3','J4','J7','SW1','D1']:c['rot']=0
# Readable functional blocks, fixed IC pitch and compact passive rows.
groups=[('USB INPUT / source detection','J1 U6 Q3 Q4 D2 R16 R17 R20 R21 R22 C15 R7 R8'),('CHARGER / 4.2V, cell NTC required','U1 L3 C1 C2 C3 C4 C6 C16 C17 R6 R11 R12 R15 J4'),('CHARGE RATE / recessed selector','SW1 R3 R4 R5'),('CELL / independent protection','J2 U5 Q2 R9 R10 C5'),('5V CONVERTER / shared 0.5A target','U2 L1 R13 R14 C7 C8 C9 C10 TP1'),('3.3V CONVERTER / 0.3A target','U3 L2 C11 C12 C13 C14 TP2 TP3'),('USB OUTPUT / attach and current limit','J7 U7 U8 R23 R24 R25 R26 R27 C18 C19 C20'),('STANDALONE RGB / voltage estimate','U9 U10 D1 R28 R29 R30 R31 R32 R33 R34 R35 C21 C22 C23'),('OPTIONAL HOST / fuel gauge and USB','J3 U4 R18 R19')]
blocks=[]
for gi,(title,refs) in enumerate(groups):
 x=8+(gi%3)*190;y=30+(gi//3)*120
 blocks.append(dict(title=title,x=x,y=y,w=184,h=114))
 big=[];small=[]
 for ref in refs.split():
  c=D[ref];(small if ref.startswith(('R','C','TP')) else big).append(c)
 for i,c in enumerate(big):c['sch']=[x+27+(i%4)*45,y+37+(i//4)*40]
 for i,c in enumerate(small):c['sch']=[x+14+(i%6)*29,y+77+(i//6)*20]
# Explicit flags for passive power inputs. Regulated outputs already power_out.
for i,net in enumerate(['USB_VBUS_IN','GND','CELL_POS','CELL_NEG','PROT_VCC']):
 c=put('#FLG'+str(i+1),'power:PWR_FLAG','PWR_FLAG','',{1:net},[0,0]);c['xy']=None;c['sch']=[18+i*35,402]
data=dict(name='AQI_Battery_Compact',width=25.7,height=88,copper_layers=2,components=cs,custom_symbols=specs,blocks=blocks,notes=[dict(text='COMPACT 18650 POWER / REV B ENGINEERING',x=10,y=10,size=2.4),dict(text='2 layers / 25.7 x 88mm. 4.2V Li-ion only. 500mA / 1A / 1.5A nominal. No host or firmware required.',x=10,y=19)],power_nets=['CHG_SYS','CELL_POS','BOOST_5V','GEN_3V3'],board_texts=[])
(out/'design.json').write_text(json.dumps(data,indent=2)+'\n')
print(len(cs),'components')
