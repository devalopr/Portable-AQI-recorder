"""Reproducible analytic review, not simulation or measured ratings."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'integrated-power/review'
r=[]
for watts in [10,15]:
 i=watts/3/.9
 r.append(dict(output_w=watts,assumed_cell_v=3,assumed_efficiency=.9,battery_a=round(i,3),old_fs8205a_pair_w_25c=round(i*i*.074,3),hsca8220_pair_w_25c=round(i*i*.013,3),hsca8220_pair_w_assumed_1p5_hot_factor=round(i*i*.013*1.5,3)))
result=dict(status='Analytic estimates only; efficiency/hot factor are assumptions, not guaranteed limits',input_reset='SY6280 EN held low by R59; CHG_IN disabled. MCU USB budget and suspend behavior still require verification.',input_1p5a_source=dict(rset_ohms=6800,nominal_limit_a=1,table_max_a_at_25c=1.25,screening_max_a_with_1percent_resistor=1.25/.99,note='Table gives 25C limit only. Budget MCU current separately; verify full temperature/cable/source behavior.'),input_3a_source=dict(rset_parallel_ohms=1/(1/6800+1/13700),nominal_limit_a=6800*(1/6800+1/13700),note='Not a battery-charge-current setting. High branch only for confirmed 3A Rp. No full-temperature maximum is provided by SY6280 source.'),protection=r,unresolved=['U5 HY2113-KB5B voltage thresholds resolved; actual ampere trip still depends on Q2','HSCA8220 sheet gives transient <=10s thermal data, not credible steady-state PCB thermal qualification','Minimum and maximum overcurrent trip across MOSFET gate voltage and temperature','3V converter-input assumption excludes protection/wiring drop; close the power balance with efficiency curve','Two-cell parallel pack and per-holder reverse insertion/equalization protection','Default-current USB/legacy charger charging path','IP5310 charge settings/CV limits/readback/startup','Input decoupling: SY6280 recommends10uF; present1uF and totalUSB attach capacitance need coordinated selection'])
(out/'power-limits.json').write_text(json.dumps(result,indent=2)+'\n')
assert result['input_1p5a_source']['screening_max_a_with_1percent_resistor']<1.5
assert .4<result['input_3a_source']['nominal_limit_a']<2
assert all(x['hsca8220_pair_w_25c']<x['old_fs8205a_pair_w_25c'] for x in r)
print(json.dumps(result,indent=2))
