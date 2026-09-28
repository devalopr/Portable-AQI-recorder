from pathlib import Path
from kicad_common import parse,ser,child,val
R=Path(__file__).resolve().parents[1]/'integrated-power';p=R/'AQI_IP5310_Power.kicad_pcb';a=parse(p.read_text())
nets={'/PROT_OD','/PROT_OC','/PROT_CS','/PROT_VCC','/LED_R','/LED_G','/LED_B','/USB_D+','/USB_D-','/HOST_USB_D+','/HOST_USB_D-'}
a[:]=[x for x in a if not(isinstance(x,list) and x[0] in ['segment','via'] and child(x,'net') and val(child(x,'net')[-1]) in nets)]
p.write_text(ser(a))
