"""Readable circuit grouping and explicit local wiring; never alters PCB files."""
from pathlib import Path
import sys,json
from kicad_common import Project,child,val,g
folder=Path(sys.argv[1]);pr=Project(folder/'design.json');D={c['ref']:c for c in pr.comps}
def pos(ref,xy):D[ref]['sch']=list(xy)
def anchor(ref,no):
 c=D[ref];x,y=map(g,c['sch']);p=next(p for p in pr.pins(c) if val(child(p,'number')[1])==str(no));a=child(p,'at');return [x+float(a[1]),y-float(a[2])]
def direct(ref,no,pts):D[ref].setdefault('direct_pins',{})[str(no)]=pts
# Connect a bank's pins to one reference component, retaining one pair of power symbols.
def bank(refs):
 for r in refs[1:]:
  for n in [1,2]:direct(r,n,[anchor(refs[0],n)])
def divider(top,bottom):
 direct(bottom,1,[anchor(top,2)])
def block(title,x,y,w,h):return dict(title=title,x=x,y=y,w=w,h=h)
if pr.name=='AQI_Main':
 pr.data['blocks']=[block('ESP32-C3 / PROGRAMMING',10,25,181,151),block('USB DATA + INTERNAL LINK',198,25,224,149),block('TFT + DIMMABLE BACKLIGHT',427,25,153,100),block('AUTOMATIC USB PRIORITY',427,129,153,67),block('INPUT POWER + 3.2 V / 3.3 V',10,180,270,164),block('PM / OPTIONAL CO2',10,347,270,62),block('MCP23008 / I2C 0x20',286,178,136,67),block('THREE FRONT BUTTONS',427,199,153,46),block('GDEY037T03 E-PAPER / ALTERNATE POPULATION',286,248,294,161)]
 pos('R21',[380,136]);pos('R22',[408,136]);pos('L3',[320,304]);pos('Q1',[455,149]);pos('Q2',[491,149]);pos('Q4',[527,149]);pos('R9',[450,178]);pos('R10',[481,178]);pos('R11',[519,178]);pos('R12',[554,178]);pos('U3',[50,219]);pos('U4',[128,218]);pos('SW4',[90,215]);pos('U9',[344,211]);pos('C17',[385,215]);pos('R30',[350,380]);D['R30']['value']='1MR'
 pos('C30',[320,270]);pos('C31',[350,270]);pos('C32',[475,270]);pos('C33',[500,270]);pos('C35',[505,302]);pos('C36',[536,302])
 # Common supply and RC banks, preserving net identity at every endpoint.
 bank(['C2','C3'])
 direct('C1',1,[[g(163),g(58)],[g(137),g(58)],anchor('R1',2)])
 for u,l,cin,ca,cb,rt,rb,shift in [('U5','L1','C9','C10','C11','R17','R18',0),('U6','L2','C12','C13','C14','R19','R20',131)]:
  pos(l,[91+shift,282]);pos(ca,[110+shift,290]);pos(cb,[135+shift,290]);pos(rt,[95+shift,317]);pos(rb,[95+shift,328.43]);bank([ca,cb]);divider(rt,rb)
  a=anchor(u,7);z=anchor(l,1);direct(u,7,[[g(77+shift),a[1]],[g(77+shift),z[1]],z])
  a=anchor(l,2);z=anchor(ca,1);direct(l,2,[[g(98+shift),a[1]],[g(98+shift),z[1]],z])
  a=anchor(u,5);z=anchor(rt,2);direct(u,5,[[g(77+shift),a[1]],[g(77+shift),z[1]],z])
 # Keep the final notes clear of the standard A2 title block.
 pr.data['notes']=[{'text':'AQI MAIN REV A / ENGINEERING PROTOTYPE - 44 x 80 mm','x':12,'y':12,'size':2.2},{'text':'TFT top contact confirmed. One display and one PM sensor. Firmware and hardware validation required before release.','x':12,'y':19}]
else:
 groups=[('USB-C / 10-PIN GH LINK',10,25,185,165),('CHARGER / USB100 DEFAULT',202,25,185,165),('CELL PROTECTION / FUEL GAUGE',395,25,187,165),('5 V BOOST / OUTPUT ENABLE',10,202,185,166),('3.3 V BUCK-BOOST',202,202,185,166),('INPUT LIMIT CONTROL / I2C 0x21',395,202,187,166)]
 pr.data['blocks']=[block(*v) for v in groups]
 positions={'J1':[50,65],'D2':[112,58],'J3':[173,63],'R1':[30,126],'R2':[60,126],'R7':[110,116],'R8':[110,133.78],'#FLG2':[164,133],'#FLG3':[165,163],'U1':[256,73],'J4':[353,60],'R3':[229,132],'R4':[262,132],'R5':[294,132],'R6':[326,132],'C1':[355,108],'C2':[355,150],'C3':[294,170],'R16':[230,169],'R17':[258,169],'U5':[447,62],'Q2':[525,65],'J2':[552,112],'R9':[416,105],'R10':[447,105],'C5':[481,106],'U4':[451,150],'C4':[526,155],'#FLG1':[557,155],'#FLG4':[411,150],'U2':[60,252],'L1':[115,235],'SW1':[52,218],'R11':[90,288],'R13':[135,265],'R14':[135,282.78],'C7':[30,293],'C8':[50,334],'C9':[90,334],'C10':[130,334],'J5':[170,320],'U3':[254,249],'L2':[316,239],'C11':[226,302],'C12':[260,302],'C13':[297,332],'C14':[332,332],'J6':[362,315],'U6':[450,248],'C15':[540,228],'R18':[518,282],'R19':[554,282],'R20':[440,332],'R21':[476,332]}
 for r,xy in positions.items():pos(r,xy)
 bank(['C8','C9','C10']);bank(['C11','C12']);bank(['C13','C14']);divider('R7','R8');divider('R13','R14')
 a=anchor('U2',5);z=anchor('L1',2);direct('U2',5,[[g(92),a[1]],[g(92),z[1]],z])
 pr.data['power_nets']=['CHG_SYS','GEN_3V3','BOOST_5V','CELL_POS','USB_VBUS_IN','PROT_VCC']
 pr.data['notes']=[{'text':'AQI BATTERY REV A / ENGINEERING PROTOTYPE - 44 x 90 mm','x':12,'y':12,'size':2.2},{'text':'65 mm unprotected cell. Observe polarity. Attach the required 10k cell NTC. Firmware must qualify USB input before increasing current.','x':12,'y':19},{'text':'5 V and 3.3 V header limits share the cell/input power budget. No reverse-cell insertion protection.','x':12,'y':382},{'text':'Fuel gauge 0x36. Battery expander 0x21. R18/R19 DNP when connected to main board.','x':12,'y':390}]
# Share one ground symbol for aligned ground pins on ICs.
for c in pr.comps:
 groups={}
 for pin in pr.pins(c):
  no=val(child(pin,'number')[1]);a=child(pin,'at')
  if c['nets'].get(no)=='GND' and float(a[3])==90:groups.setdefault(float(a[2]),[]).append(no)
 for pins in groups.values():
  for no in pins[1:]:direct(c['ref'],no,[anchor(c['ref'],pins[0])])
(folder/'schematic-layout.json').write_text(json.dumps({'positions':{r:c['sch'] for r,c in D.items()},'blocks':pr.data['blocks']},indent=2))
pr.schematic()
