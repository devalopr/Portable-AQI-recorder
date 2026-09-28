"""Rev B main board cost estimate (run with KiCad Python for the joint count).

Inputs: review/jlc-bom.csv (DNP excluded), review/price-snapshot-2026-09-27.json (LCSC tiers, USD),
AQI_Main.kicad_pcb (solder joints). Output: review/COST.md. Not a quotation.
"""
from pathlib import Path
import csv, json, math
import pcbnew as pcb

root = Path(__file__).resolve().parents[1] / 'main'
INR = 96.0                        # planning rate used across this repo
# JLCPCB published fees (help/article/pcb-assembly-price, 2026-09): Standard PCBA, double-sided.
SETUP, STENCIL, FEEDER, HAND_ORDER = 51.12, 16.42, 1.53, 3.58
THT_JOINT = 0.0164
# Fabrication, all-in per m2 at volume and per 5-piece prototype order (<100x100 mm), by copper layer count.
FAB_PER_M2 = {4: 84.2, 2: 35.0}   # 4L: JLC 500-pc example ($421.10 / 5 m2); 2L: JLC volume, ~INR 6-12 per battery board
FAB_PROTO_5 = {4: 8.0, 2: 2.0}    # typical list prices (promos can be lower)


def smt_rate(joints):
    return 0.0016 if joints <= 50000 else (0.0013 if joints <= 100000 else 0.0012)


def unit(tiers, n):
    price = tiers[0]['price']
    for t in tiers:
        if n >= int(t['qty'].rstrip('+')):
            price = t['price']
    return price


def main():
    snap = json.loads((root / 'review/price-snapshot-2026-09-27.json').read_text())['parts']
    rows = [r for r in csv.DictReader(open(root / 'review/jlc-bom.csv')) if r['LCSC']]
    b = pcb.LoadBoard(str(root / 'AQI_Main.kicad_pcb'))
    layers = b.GetCopperLayerCount()
    e = b.GetBoardEdgesBoundingBox()
    w_mm, h_mm = pcb.ToMM(e.GetWidth()), pcb.ToMM(e.GetHeight())
    area_m2 = w_mm * h_mm / 1e6
    smd = tht = 0
    for f in b.GetFootprints():
        if f.IsDNP() or f.GetReference().startswith('TP'):
            continue
        for p in f.Pads():
            if p.GetAttribute() == pcb.PAD_ATTRIB_SMD:
                smd += 1
            elif p.GetAttribute() == pcb.PAD_ATTRIB_PTH:
                tht += 1
    out = {}
    for n in (5, 1000):
        parts = []
        for r in rows:
            q = int(r['Qty']); d = snap[r['LCSC']]
            u = unit(d['prices'], q * n)
            parts.append((r['Designator'], r['Comment'], r['LCSC'], d['library_type'], q, u, u * q))
        p_total = sum(x[6] for x in parts)
        fab = FAB_PROTO_5[layers] / n if n <= 5 else FAB_PER_M2[layers] * area_m2
        asm_fixed = SETUP + STENCIL + FEEDER * len(rows) + HAND_ORDER
        asm = asm_fixed / n + smd * smt_rate(smd * n) + tht * THT_JOINT
        out[n] = dict(parts=parts, p_total=p_total, fab=fab, asm=asm, total=p_total + fab + asm)
    lines = ['# Main board Rev B — cost estimate', '',
             'Catalogue snapshot 2026-09-27 (PCBParts JLC/LCSC, `price-snapshot-2026-09-27.json`), USD, '
             f'INR at {INR:.0f}/USD. Default TFT + SEN5x/SEN6x build; DNP parts (the SCD41 U8 and the J6/J8 headers) excluded; the CO2 supply (U7, C15, C16, C42) is fitted. '
             'JLCPCB Standard PCBA, double-sided (buttons on the front, everything else including USB-C on the back). Not a quotation.', '',
             f'Solder joints per board: {smd} SMT, {tht} through-hole. {len(rows)} unique placed parts.', '',
             '| Per board | 5 prototypes | 1000 boards |', '|---|---:|---:|']
    for k, label in [('p_total', 'Parts'), ('fab', f'PCB fabrication ({layers}-layer, {w_mm:.0f} x {h_mm:.0f} mm)'),
                     ('asm', 'Assembly (setup, stencil, feeders, joints)'), ('total', '**Total**')]:
        a, z = out[5][k], out[1000][k]
        lines.append(f'| {label} | ${a:.2f} (INR {a*INR:.0f}) | ${z:.2f} (INR {z*INR:.0f}) |')
    lines += ['', 'Excludes shipping, import duty and GST, programming/test, the display, PM/CO2 sensors, '
              'enclosure and the battery board. JLC may add attrition parts; small orders also pay per-order minimums.',
              '', '## Parts at 1000 boards', '', '| Refs | Part | LCSC | Library | Qty | Unit $ | Line $ |',
              '|---|---|---|---|---:|---:|---:|']
    for d, c, l, lib, q, u, t in sorted(out[1000]['parts'], key=lambda x: -x[6]):
        lines.append(f'| {d} | {c} | {l} | {lib} | {q} | {u:.4f} | {t:.3f} |')
    (root / 'review/COST.md').write_text('\n'.join(lines) + '\n')
    for n in (5, 1000):
        o = out[n]
        print(f'{n:>5} boards: parts ${o["p_total"]:.2f}  fab ${o["fab"]:.2f}  assembly ${o["asm"]:.2f}  '
              f'total ${o["total"]:.2f} (INR {o["total"]*INR:.0f})')


if __name__ == '__main__':
    main()
