"""Authoritative main-board component/net contract. Generate JSON, then KiCad."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from kicad_common import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'main'
cs=[]
def add(ref,lib,value,nets,sch,xy,fp=None,rot=0,side='back',dnp=False,**kw):
 c=dict(ref=ref,lib=lib,value=value,nets={str(k):v for k,v in nets.items()},sch=sch,xy=xy,rot=rot,side=side,dnp=dnp,**kw)
 if fp:c['fp']=fp
 cs.append(c);return c
RFP='Resistor_SMD:R_0603_1608Metric';CFP='Capacitor_SMD:C_0603_1608Metric';C8='Capacitor_SMD:C_0805_2012Metric'
def r(n,v,a,b,sch,xy,**kw):return add('R'+str(n),'Device:R_Small_US',v,{1:a,2:b},sch,xy,RFP,**kw)
def c(n,v,a,b,sch,xy,fp=CFP,**kw):return add('C'+str(n),'Device:C',v,{1:a,2:b},sch,xy,fp,**kw)
def mos(n,gate,drain,sch,xy):return add('Q'+str(n),'Transistor_FET:2N7002','AO3400A',{1:gate,2:'GND',3:drain},sch,xy,'Package_TO_SOT_SMD:SOT-23',mpn='AO3400A',manufacturer='Alpha & Omega Semiconductor',datasheet='https://www.aosmd.com/sites/default/files/res/data_sheets/AO3400A.pdf')
# Embed official Espressif symbol, preserving pin numbers/names and geometry.
raw=parse((ROOT/'references/Espressif.kicad_sym').read_text());es=next(s for s in children(raw,'symbol') if val(s[1])=='ESP32-C3-MINI-1')
es=copy.deepcopy(es);es[1]=q('ESP32-C3-MINI-1-H4')
for un in children(es,'symbol'):un[1]=q(val(un[1]).replace('ESP32-C3-MINI-1','ESP32-C3-MINI-1-H4'))
(OUT/'lib/Espressif-H4.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '+ser(es)+')')
# custom import path specified for generator; pin contract uses official symbol.
pn={str(i):None for i in range(1,54)}
for n in [1,2,11,14,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53]:pn[str(n)]='GND'
pn.update({str(k):v for k,v in {3:'+3V2',5:'BOOT_GPIO2',6:'BL_PWM',8:'MCU_EN',12:'I2C_SDA',13:'I2C_SCL',16:'DISP_CS',18:'DISP_SCK',19:'DISP_DC',20:'DISP_MOSI',21:'DISP_RST',22:'BOOT_GPIO8',23:'BOOT_GPIO9',26:'USB_MCU_D-',27:'USB_MCU_D+',30:'EPD_BUSY',31:'UART_TX'}.items()})
add('U1','AQI:ESP32-C3-MINI-1-H4','ESP32-C3-MINI-1-H4',pn,(74,80),(35,68),'AQI:ESP32-C3-MINI-1',rot=180,mpn='ESP32-C3-MINI-1-H4',manufacturer='Espressif',datasheet='https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.html')
r(1,'10kR','+3V2','MCU_EN',(137,45),(26,69));c(1,'1uF 16V','MCU_EN','GND',(163,45),(26,71));c(2,'10uF 25V','+3V2','GND',(137,75),(26,73),C8);c(3,'100nF 25V','+3V2','GND',(163,75),(26,75))
r(2,'10kR','+3V2','BOOT_GPIO9',(137,105),(27,65));r(3,'10kR','+3V2','BOOT_GPIO8',(163,105),(29,65));r(4,'10kR','+3V2','BOOT_GPIO2',(137,133),(31,65))
# service pads, boot and reset can be shorted to nearby ground during recovery.
for i,(net,x,y) in enumerate([('GND',4,74),('MCU_EN',7,74),('BOOT_GPIO9',10,74),('UART_TX',13,74),('EPD_BUSY',16,74),('+3V2',19,74)],1):
 add('TP'+str(i),'Connector:TestPoint',net,{1:net},(23+(i-1)*28,152),(x,y),'TestPoint:TestPoint_Pad_D1.0mm')
# Local USB and combined GH input
un={p:'GND' for p in ['A1','A12','B1','B12','SH']};un.update({p:'+5V_USB' for p in ['A4','A9','B4','B9']});un.update({'A5':'USB_CC1','B5':'USB_CC2','A6':'USB_LOCAL_D+','B6':'USB_LOCAL_D+','A7':'USB_LOCAL_D-','B7':'USB_LOCAL_D-','A8':None,'B8':None})
add('J1','Connector:USB_C_Receptacle_USB2.0_16P','USB-C / standalone',un,(236,69),(7,78.5),'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',side='front',mpn='USB4105-GF-A',manufacturer='GCT')
gh={1:'+5V_INT',2:'+5V_INT',3:'GND',4:'USB_INT_D-',5:'USB_INT_D+',6:'GND',7:'I2C_SDA',8:'I2C_SCL',9:'GND',10:'INT_HOST_PRESENT'}
add('J2','Connector_Generic:Conn_01x10','BATTERY / JST GH',gh,(393,53),(40,52),'Connector_JST:JST_GH_SM10B-GHS-TB_1x10-1MP_P1.25mm_Horizontal',rot=90,mpn='SM10B-GHS-TB(LF)(SN)',manufacturer='JST')
r(5,'5.1kR','USB_CC1','GND',(210,132),(3,77));r(6,'5.1kR','USB_CC2','GND',(236,132),(5,77));c(4,'1uF 16V','+5V_USB','GND',(262,132),(10,78))
add('D1','Power_Protection:USBLC6-2SC6','USBLC6-2SC6',{1:'USB_LOCAL_D+',6:'USB_LOCAL_D+',3:'USB_LOCAL_D-',4:'USB_LOCAL_D-',2:'GND',5:'+5V_USB'},(292,52),(10,74),'Package_TO_SOT_SMD:SOT-23-6',mpn='USBLC6-2SC6',manufacturer='STMicroelectronics')
add('U2','Interface_USB:TS3USB30EDGSR','TS3USB30EDGSR',{1:'USB_SEL_INT',2:'USB_LOCAL_D+',3:'USB_INT_D+',4:'USB_SWITCH_D+',5:'GND',6:'USB_SWITCH_D-',7:'USB_INT_D-',8:'USB_LOCAL_D-',9:'USB_OE_N',10:'+3V2'},(323,100),(20,72),mpn='TS3USB30EDGSR',manufacturer='Texas Instruments')
r(7,'22R','USB_SWITCH_D+','USB_MCU_D+',(291,150),(24,72));r(8,'22R','USB_SWITCH_D-','USB_MCU_D-',(320,150),(24,74));c(5,'100nF 25V','+3V2','GND',(351,150),(18,73))
# Discrete hardware priority: S=!LOCAL, OE=!(LOCAL|INTERNAL). No firmware needed to enumerate.
mos(1,'+5V_USB','USB_SEL_INT',(455,142),(13,70));mos(2,'+5V_USB','USB_OE_N',(491,142),(13,67));mos(4,'INT_HOST_PRESENT','USB_OE_N',(527,142),(17,67))
r(9,'47kR','+3V2','USB_SEL_INT',(450,180),(12,72));r(10,'47kR','+3V2','USB_OE_N',(481,180),(14,72));r(11,'1MR','INT_HOST_PRESENT','GND',(519,180),(19,66));r(12,'100kR','+5V_USB','GND',(554,180),(11,76))
# Power mux, main rail switch, core and sensor bucks.
add('U3','Power_Management:TPS2116DRL','TPS2116DRLR',{1:'GND',2:'+5V_SYS',7:'+5V_SYS',3:'+5V_USB',4:'PWR_PR1',5:'+5V_USB',6:'+5V_INT',8:None},(50,205),(15,58),mpn='TPS2116DRLR',manufacturer='Texas Instruments')
r(13,'301kR','+5V_USB','PWR_PR1',(22,251),(13,56));r(14,'100kR','PWR_PR1','GND',(48,251),(13,60));c(6,'1uF 16V','+5V_INT','GND',(75,251),(17,59));c(7,'10uF 25V','+5V_SYS','GND',(100,251),(17,56),C8)
add('SW4','Switch:SW_SPDT','POWER / JS102011SAQN',{1:'+5V_SYS',2:'MAIN_ON',3:'GND'},(90,201),(2,58),'Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN',rot=270,mpn='JS102011SAQN',manufacturer='C&K')
add('U4','Power_Management:TPS22917DBV','TPS22917DBVR',{1:'+5V_SYS',2:'GND',3:'MAIN_ON',4:'MAIN_CT',5:'MAIN_QOD',6:'+5V_SW'},(128,204),(21,58),mpn='TPS22917DBVR',manufacturer='Texas Instruments')
r(15,'100kR','MAIN_ON','GND',(130,251),(20,62));r(16,'100R','+5V_SW','MAIN_QOD',(158,251),(23,60));c(8,'1nF 25V','MAIN_CT','GND',(185,251),(20,55))
for base,xs,ys,xp,yp,out,rt in [(0,52,292,31,52,'+3V2','300kR'),(1,183,292,33,22,'+3V3_PM','316kR')]:
 u=5+base;ln=1+base;rid=17+base*2;cid=9+base*3;sn='CORE' if base==0 else 'PM'
 add('U'+str(u),'Regulator_Switching:TPS62160DGK','TPS62160DGKR',{1:'GND',2:'+5V_SW',3:'+5V_SW',4:'GND',5:sn+'_FB',6:out,7:sn+'_SW',8:None},(xs,ys),(xp,yp),mpn='TPS62160DGKR',manufacturer='Texas Instruments')
 add('L'+str(ln),'Device:L','2.2uH SWPA4020S',{1:sn+'_SW',2:out},(xs+39,ys-6),(xp+5,yp),'Inductor_SMD:L_Sunlord_SWPA4020S',mpn='SWPA4020S2R2MT',manufacturer='Sunlord')
 r(rid,rt,out,sn+'_FB',(xs+11,ys+28),(xp+1,yp+4));r(rid+1,'100kR',sn+'_FB','GND',(xs+42,ys+28),(xp-1,yp+4))
 c(cid,'10uF 25V','+5V_SW','GND',(xs-27,ys+6),(xp-4,yp),C8);c(cid+1,'22uF 10V',out,'GND',(xs+73,ys-6),(xp+6,yp+4),C8);c(cid+2,'100nF 25V',out,'GND',(xs+73,ys+25),(xp+3,yp+5))
# Sensor connectors are physically different so 5V cannot accidentally reach SEN6x.
add('J3','Connector_Generic:Conn_01x06','SEN5x / 5V', {1:'+5V_SW',2:'GND',3:'I2C_SDA',4:'I2C_SCL',5:'GND',6:None},(35,368),(4,24),'Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal',rot=270,mpn='SM06B-GHS-TB(LF)(SN)',manufacturer='JST')
add('J4','Connector_Generic:Conn_01x04','SEN6x / 3.3V',{1:'+3V3_PM',2:'GND',3:'I2C_SDA',4:'I2C_SCL'},(77,369),(4,43),'Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal',rot=270,mpn='SM04B-GHS-TB(LF)(SN)',manufacturer='JST',note='Custom 4-to-6 cable. Sensor pins5/6 open; pin1 3.3V,2GND,3SDA,4SCL.')
# Quiet SCD4x LDO from switched5V ensures dropout headroom; optional entire population.
add('U7','AQI:TPS7A2033DBV','TPS7A2033PDBVR',{1:'+5V_SW',2:'GND',3:'+5V_SW',4:None,5:'+3V3_CO2'},(138,369),(11,10),'Package_TO_SOT_SMD:SOT-23-5',dnp=True,mpn='TPS7A2033PDBVR',manufacturer='Texas Instruments')
c(15,'1uF 16V','+5V_SW','GND',(110,390),(8,9),dnp=True);c(16,'10uF 25V','+3V3_CO2','GND',(169,390),(9,15),C8,dnp=True)
add('U8','Sensor_Gas:SCD40-D-R2','SCD41-D-R2',{6:'GND',7:'+3V3_CO2',9:'I2C_SCL',10:'I2C_SDA',19:'+3V3_CO2',20:'GND',21:'GND'},(220,373),(10,14),dnp=True,mpn='SCD41-D-R2',manufacturer='Sensirion',note='Optional; vented sensor body 10.1x10.1mm, clearance and thermal review required')
# Buttons and I2C pull-ups
add('U9','Interface_Expansion:MCP23008-xSO','MCP23008-E/SO',{1:'I2C_SCL',2:'I2C_SDA',3:'GND',4:'GND',5:'GND',6:'MCU_EN',7:None,8:None,9:'GND',10:'BUTTON_LEFT',11:'BUTTON_OK',12:'BUTTON_RIGHT',13:None,14:None,15:None,16:None,17:None,18:'+3V2'},(344,193),(27,43),mpn='MCP23008-E/SO',manufacturer='Microchip')
c(17,'100nF 25V','+3V2','GND',(385,194),(27,49));r(21,'4.7kR','+3V2','I2C_SDA',(386,136),(22,48));r(22,'4.7kR','+3V2','I2C_SCL',(416,136),(24,48))
for i,(n,x) in enumerate([('LEFT',8),('OK',22),('RIGHT',36)],1):
 add('SW'+str(i),'Switch:SW_Push',n,{1:'BUTTON_'+n,2:'GND'},(439+(i-1)*48,210),(x,66),'Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2',side='front',mpn='KMR221GLFS',manufacturer='C&K')
 r(22+i,'10kR','+3V2','BUTTON_'+n,(439+(i-1)*48,235),(x,62))
# Backlight driver: 0.1V/1.5R =66.7mA nominal, <=~74mA at+10%reference/1%R.
add('U10','AQI:STCS05A','STCS05ADR',{1:'+5V_SW',2:'BL_PWM',3:'+3V2',4:'BL_K',5:'BL_FB',6:'GND',7:None,8:None},(472,82),(31,12),'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',mpn='STCS05ADR',manufacturer='STMicroelectronics')
r(26,'1.5R','BL_FB','GND',(449,111),(31,18));r(27,'100kR','BL_PWM','GND',(480,111),(26,18));c(18,'100nF 25V','+5V_SW','GND',(509,111),(26,12));c(19,'470nF 16V','BL_K','GND',(545,111),(36,16));r(28,'0R','+5V_SW','BL_A',(552,80),(36,12))
custom=[{'name':'TPS7A2033DBV','pins':[{'number':n,'name':name,'type':typ,'side':side} for n,name,typ,side in [(1,'IN','power_in','left'),(2,'GND','power_in','bottom'),(3,'EN','input','left'),(4,'NC','no_connect','right'),(5,'OUT','power_out','right')]]},{'name':'STCS05A','pins':[{'number':n,'name':name,'type':typ,'side':side} for n,name,typ,side in [(1,'VCC','power_in','top'),(2,'PWM','input','left'),(3,'EN','input','left'),(4,'DRAIN','passive','right'),(5,'FB','passive','right'),(6,'GND','power_in','bottom'),(7,'SLOPE','passive','left'),(8,'DISC','open_collector','right')]]}]
# TFT is included immediately; EPD fragment merged after the independent review corrections.
disp=json.loads((OUT/'display-fragment.json').read_text())
for co in disp['components']:
 if co['ref']=='C37': continue
 if co['ref']=='J5':
  co['sch']=[565,48];co['value']='TFT TOP CONTACT';co['fp']='Connector_FFC-FPC:TE_1-84953-0_1x10-1MP_P1.0mm_Horizontal';co['mpn']='1-84953-0';co['manufacturer']='TE Connectivity'
 else:
  co['nets']={str(k):({'EPD_RST':'DISP_RST','EPD_DC':'DISP_DC','EPD_CS':'DISP_CS'}.get(v,v)) for k,v in co['nets'].items()}
  co['value']=co['value'].split(' EPD')[0].replace('GDEY037T03 UC8253 24P 0.5mm','GDEY037T03').replace(' UC8253 boost MOSFET','')
 cs.append(co)
# Flags declare the external input supplies and power after passive interconnect.
for i,(net,pos) in enumerate([('+5V_USB',(212,24)),('+5V_INT',(368,24)),('GND',(278,24)),('+3V2',(157,170)),('+3V3_PM',(188,170))],1):
 add('#FLG'+str(i),'power:PWR_FLAG','PWR_FLAG',{1:net},pos,None,side='front')
D={'name':'AQI_Main','width':44,'height':80,'components':cs,'custom_symbols':custom,'import_symbols':[{'path':'lib/Espressif-H4.kicad_sym','name':'ESP32-C3-MINI-1-H4','libid':'AQI:ESP32-C3-MINI-1-H4'}], 'blocks':[], 'notes':[{'text':'AQI MAIN / REV A - ENGINEERING PROTOTYPE','x':12,'y':10,'size':2.4},{'text':'TFT top contact confirmed by user. EPD population alternative. One PM module. USB source-current qualification required.','x':12,'y':17}], 'board_texts':[{'text':'AQI MAIN A','xy':[22,60],'layer':'F_SilkS'},{'text':'L','xy':[8,70]},{'text':'OK','xy':[22,70]},{'text':'R','xy':[36,70]}], 'envelopes':[{'start':[.64,1.5],'end':[43.36,62.46]}], 'keepouts':[[[27.5,73],[44,73],[44,80],[27.5,80]]]}
if (OUT/'placement.json').exists():
 moves=json.loads((OUT/'placement.json').read_text())
 for cc in D['components']:
  if cc['ref'] in moves:cc.update(moves[cc['ref']])
(OUT/'design.json').write_text(json.dumps(D,indent=2))
print(len(cs),'main components')
