"""Create a separate main-board schematic for the PWM battery interface."""
from pathlib import Path
import json,shutil,copy
from kicad_common import Project
root=Path(__file__).resolve().parents[1]
src=root.parent/'rev-a/main';out=root/'main-pwm';out.mkdir(exist_ok=True)
shutil.copytree(src/'lib',out/'lib',dirs_exist_ok=True)
shutil.copy2(src/'AQI_Main.kicad_pro',out/'AQI_Main.kicad_pro')
shutil.copy2(src/'fp-lib-table',out/'fp-lib-table')
d=json.loads((src/'design.json').read_text());D={c['ref']:c for c in d['components']}
D['J2']['nets'].update({'7':'BAT_PWM','8':None})
D['J2']['value']='BATTERY / GH PWM'
D['U1']['nets']['31']='BAT_PWM_MCU'
D['TP4'].update(value='BAT_PWM_MCU',nets={'1':'BAT_PWM_MCU'})
for ref,value,nets,sch in [('R33','10kR',{'1':'+3V2','2':'BAT_PWM'},[470,300]),('R34','1kR',{'1':'BAT_PWM','2':'BAT_PWM_MCU'},[515,300])]:
 c=copy.deepcopy(D['R17']);c.update(ref=ref,value=value,nets=nets,sch=sch,xy=None,mpn='',manufacturer='',note='PWM interface; host pullup and GPIO21 boot-UART contention limiting.');d['components'].append(c)
d['notes'].append(dict(text='PWM BATTERY REVISION: GH7 BAT_PWM, GH8 NC. GPIO21 input; USB logs only. PCB routing pending.',x=12,y=410))
d['telemetry']={'gpio':21,'gh_pin':7,'reserved_nc_pin':8,'pullup_ohms':10000,'series_ohms':1000,'frequency_hz':100,'high_duty_range':[0.1,0.9],'replaces':'UART TX testpad function only; native USB and EPD BUSY retained'}
(out/'design.json').write_text(json.dumps(d,indent=2)+'\n')
Project(out/'design.json').schematic()
print(out)
