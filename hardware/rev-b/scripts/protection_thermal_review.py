"""Manufacturer thresholds and constant-power screening; no thermal pass claimed."""
import json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'integrated-power/review'
rows=[]
for p in [10,15]:
 for v in [3,3.6,4.2]:
  for eta in [.85,.9]:
   # Maximum 25C Rds multiplied by an explicitly assumed hot factor.
   r=.013*1.5
   i=(v-math.sqrt(v*v-4*r*p/eta))/(2*r)
   rows.append(dict(output_w=p,cell_v=v,assumed_efficiency=eta,assumed_hot_pair_ohms=r,battery_a=round(i,4),protected_input_v=round(v-i*r,4),fet_loss_w=round(i*i*r,4),minimum_gate_v_screen=round(v-.1-i*r,4),screening_trip_lower_a=round(.125/r,4),margin_to_screening_trip_a=round(.125/r-i,4)))
result=dict(source='HY2113 V16_EN pp8,10-13,17; HSCA8220 V3.0 pp1-3',status='IC voltage thresholds resolved. Current/thermal values are screening calculations, not guaranteed pack ratings.',part='HY2113-KB5B / C168771',thresholds_25c=dict(overcharge_v=[4.225,4.25,4.275],overdischarge_v=[2.75,2.8,2.85],overdischarge_release_v=[2.95,3,3.05],discharge_sense_mv=[135,150,165],charge_sense_mv=[-120,-100,-80]),thresholds_minus20_to60c=dict(overcharge_v=[4.215,4.25,4.285],overdischarge_v=[2.735,2.8,2.865],overdischarge_release_v=[2.915,3,3.085],discharge_sense_mv=[125,150,175],note='Datasheet table9: guaranteed by design, not screened in production; excludes full -40..85 range'),typical_delays_ms=dict(overcharge=1000,overdischarge=145,discharge_overcurrent=24,charge_overcurrent=16,short_circuit=.3),supply_filter=dict(r9_ohm=100,c5_f=1e-7,maximum_6ua_supply_drop_mv=.6),screening=rows,unresolved=['No guaranteed minimum MOSFET Rds: cannot calculate guaranteed upper overcurrent trip from its maximum resistance','Hot factor1.5 is an assumption; no verified steady-state thermal resistance for this PCB','Source model includes MOSFET drop but omits holder/contact/trace/cell internal resistance','Short-circuit pulse energy and cell capability must be coordinated before production','Do not use 4.25V protection cutoff as charger CV target; program IP5310 conservatively and measure overshoot','Exact IP5310 reset defaults must be safe before firmware starts','Firmware low-cell cutoff needs margin above independent protector; provisional3.1V loaded, recovery3.3V is not implemented'])
(out/'protection-thermal-review.json').write_text(json.dumps(result,indent=2)+'\n')
assert all(x['minimum_gate_v_screen']>=2.5 for x in rows)
print(json.dumps({'part':result['part'],'worst_screening_case':rows[6]},indent=2))
