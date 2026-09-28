"""Reproducible architecture estimate, NOT an assembly BOM or supplier quote.

No KiCad files are changed. Catalogue candidates and engineering allowances are
kept separate. Quantity is 1,000 boards of each variant; currency basis INR96/USD.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATE = 96
# One of each per board. Exact candidate parts; not yet circuit-approved.
items = [
    ('Integrated charger/boost', 'IP5310_I2C', 'C20616661', .3304, '1000+', 'OUT OF STOCK; replenishment quote required'),
    ('MCU', 'CH32V003F4P6', 'C5187096', .1627, '500+', 'existing selection'),
    ('3.3V buck IC', 'SY8089A1AAC', 'C479074', .0542, 'handoff', 'existing candidate'),
    ('Input USB-C', 'TYPE-C 16PIN 2MD(073)', 'C2765186', .0506, 'handoff', 'footprint pending'),
    ('Output USB-C', 'TYPE-C 6P', 'C456012', .0236, 'handoff', 'USB port implementation under review'),
    ('GH connector', 'SM10B-GHS-TB', 'C2683602', .1952, 'handoff', 'genuine JST retained in estimate'),
    ('USB data ESD', 'USBLC6-2SC6-ES', 'C5180249', .0225, '600+', 'unqualified lower-cost candidate'),
    ('Input CC detector', 'HUSB320-BA000-QN12R', 'C7471906', .1968, 'handoff', 'retained conservatively; possible integration saving NOT deducted'),
    ('Input limiter', 'SY6280AAAC', 'C207620', .0593, 'handoff', 'input-current range/thermal qualification pending'),
    ('Output CC + switch', 'HUSB305-01', 'C7471917', .2033, '1000+', 'candidate for 1.5A/3A USB advertisement; not applied'),
]
# These figures are explicit engineering budget allowances, NOT sourced prices.
# They cannot establish a ceiling or replace a line-by-line schematic BOM/quote.
allowances = [
    ('Two inductors, power capacitors and remaining decoupling', 12, 26),
    ('Protection IC, power/signal MOSFETs, resistors, optional NTC provision', 8, 18),
    ('Three-position selector and dim RGB LED', 4, 10),
    ('Two-layer bare PCB: one-cell geometry', 6, 12),
    ('Assembly including holder, setup and attrition amortized', 10, 25),
    ('Programming and functional test', 5, 12),
]

priced = round(sum(x[3] for x in items) * RATE, 4)
variants = []
for cells, total_a, usb_a in [(1, 2, 1.5), (2, 3, 3)]:
    holder = 30 * cells  # user allowance; two-cell estimate uses two individual holders
    extra_pcb = (0, 0) if cells == 1 else (4, 10)
    low = priced + holder + sum(x[1] for x in allowances) + extra_pcb[0]
    high = priced + holder + sum(x[2] for x in allowances) + extra_pcb[1]
    variants.append(dict(cells_parallel=cells, total_5v_rating_a=total_a,
                         usb_c_rating_a=usb_a, holder_allowance_inr=holder,
                         engineering_estimate_inr=[round(low, 2), round(high, 2)],
                         caveat='Shared power budget; no exact two-cell holder or PCB geometry selected'))
result = dict(date='2026-09-12', boards_per_variant=1000, inr_per_usd=RATE,
              status='ARCHITECTURE ESTIMATE ONLY; no schematic release or manufacturing quotation',
              excluded=['cells', 'enclosure', 'cables', 'packaging', 'freight', 'tax',
                        'certification', 'development and prototype costs'],
              candidates=[dict(role=a, mpn=b, lcsc=c, usd=d, tier=e, status=f,
                               inr=round(d*RATE, 4)) for a,b,c,d,e,f in items],
              priced_candidates_subtotal_inr=priced,
              unquoted_allowances=[dict(category=a, low_inr=b, high_inr=c) for a,b,c in allowances],
              variants=variants)
out = ROOT/'references/common-stage-cost-estimate.json'
out.write_text(json.dumps(result, indent=2)+'\n')
lines = ['# Common power-stage architecture estimate', '',
         '2026-09-12. 1,000 boards per variant, INR96/USD. This is not a schematic-derived BOM or supplier quote.', '',
         '| Candidate | MPN / LCSC | INR per board | Status |', '|---|---|---:|---|']
for a,b,c,d,e,f in items:
    lines.append(f'| {a} | {b} / {c} | {d*RATE:.2f} | {f} |')
lines += ['', f'Catalogue-candidate subtotal: **INR{priced:.2f}**, without holder or the categories below.', '',
          '| Unquoted engineering allowance | INR low | INR high |', '|---|---:|---:|']
for a,b,c in allowances: lines.append(f'| {a} | {b} | {c} |')
lines += ['', 'Holder allowance: INR30 per holder from user sourcing. Two-cell estimate assumes two separate holders and INR4–10 additional PCB allowance.', '',
          '| Variant | Estimated assembled cost, INR |', '|---|---:|']
for v in variants:
    lo,hi=v['engineering_estimate_inr'];lines.append(f"| {v['cells_parallel']} cell(s) | {lo:.2f}–{hi:.2f} |")
lines += ['', '**These ranges are planning estimates, not cost guarantees.** Multiple parts are unqualified, the selected integrated variant has zero catalogue stock, and all manufacturing allowances are unquoted. No INR200 factory-cost claim is established.', '',
          'Potential savings not deducted: integrating input CC detection, qualifying a cheaper GH-compatible connector, further passive consolidation and assembly quotation. Do not remove electrical functions solely to make the spreadsheet reach the target.', '',
          'Excludes cells, enclosure, cables, packaging, freight, tax, certification, development and prototypes. Original BOM handoff metadata and all KiCad files are unchanged.']
(ROOT/'references/common-stage-cost-estimate.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'priced_candidates_inr':priced,'variants':variants},indent=2))

# Separate what-if analysis: never substitute unqualified parts in the assembly BOM.
cc_removed = .1968 * RATE
gh_saving = (.1952 - .0529) * RATE  # C54618749, 300+ tier at quantity 1000
scenarios = []
for v in variants:
    lo, hi = v['engineering_estimate_inr']
    scenarios.append(dict(cells_parallel=v['cells_parallel'],
        input_adc_only_inr=[round(lo-cc_removed+2,2), round(hi-cc_removed+5,2)],
        input_adc_and_candidate_gh_inr=[round(lo-cc_removed+2-gh_saving,2),
                                      round(hi-cc_removed+5-gh_saving,2)]))
study = dict(date='2026-09-12', status='UNQUALIFIED COST-REDUCTION SCENARIOS',
    input_cc_removed_inr=round(cc_removed,4),
    additional_adc_frontend_allowance_inr=[2,5],
    adc_allowance_status='Unquoted incremental hardware allowance, not verified circuit cost; firmware development excluded',
    gh_candidate=dict(mpn='LQ-GH1.25-10PWT',lcsc='C54618749',usd=.0529,
                      tier='300+',stock_observed=5225,
                      status='Manufacturer drawing and locking/mating qualification still required'),
    gh_saving_inr=round(gh_saving,4),variants=scenarios)
(ROOT/'references/cc-cost-scenarios.json').write_text(json.dumps(study,indent=2)+'\n')
print(json.dumps(study,indent=2))
