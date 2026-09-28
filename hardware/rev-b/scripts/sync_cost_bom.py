"""Synchronize sourcing metadata, preserving schematic circuitry and layout.

Run with KiCad's bundled Python. CSV output is exported by kicad-cli from
the annotated schematic, never maintained independently.
"""
import copy
import json
import subprocess
from pathlib import Path
from kicad_common import parse, ser, val, child, children, q

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'references/pricing-1000pcs-2026-09-11.json'
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'


def annotate_design(data):
    snapshot = json.loads(SNAPSHOT.read_text())
    lookup = {ref: row for row in snapshot['rows'] for ref in row['refs']}
    unresolved = {ref.strip(): reason for refs, _, reason in snapshot['unresolved']
                  for ref in refs.split(',')}
    for c in data['components']:
        ref = c['ref']
        if ref.startswith(('#', 'TP')):
            continue
        fields = {'Procurement status': 'UNRESOLVED',
                  'Price basis': '1000 boards; catalogue tiers; INR96/USD; excludes assembly/tax'}
        if c.get('dnp'):
            fields['Procurement status'] = 'DNP'
        elif ref == 'J2':
            c.update(value='Generic 18650 SMT holder', mpn='UNSPECIFIED - supplier confirmation required',
                     manufacturer='Generic / Blossom per user', lcsc='')
            c['note'] = ('User-sourced below INR30; INR30 costing allowance. Body 77.5x21.5mm; '
                         '87mm including terminals; terminal width 6.5mm. Existing Keystone footprint '
                         'is a placeholder requiring replacement/fit validation. 15417 is a retailer SKU, not a verified MPN.')
            fields.update({'Procurement status': 'USER-SOURCED; FOOTPRINT PENDING',
                           'Budget INR each': '30.00', 'Price basis': 'User-confirmed under INR30; conservative allowance'})
        elif ref in lookup:
            row = lookup[ref]
            part = snapshot['parts'][row['id']]
            fields.update({'Budget USD each': format(row['unit'], '.4f'),
                           'Budget INR each': format(row['unit'] * 96, '.4f'),
                           'Price source': row['url'], 'Price date': snapshot['date'],
                           'Catalogue stock': str(row['stock'])})
            if ref in ('J1', 'J7'):
                fields.update({'Procurement status': 'REPLACEMENT CANDIDATE; FOOTPRINT PENDING',
                               'Candidate MPN': row['mpn'], 'Candidate LCSC': row['id'],
                               'Candidate Manufacturer': part['manufacturer']})
            else:
                c.update(mpn=row['mpn'], manufacturer=part['manufacturer'], lcsc=row['id'])
                fields['Procurement status'] = ('NOMINAL SPEC MATCH; DC-BIAS QUALIFICATION PENDING'
                                                 if ref.startswith('C') else 'CATALOGUE MATCH')
                if row['stock'] < row['orderqty']:
                    fields['Procurement status'] += '; STOCK BELOW ORDER QUANTITY'
                if ref.startswith('R') and 'exact procurement part pending' in c.get('note', ''):
                    c['note'] = 'Exact nominal resistance/tolerance and 0603 package matched; see MPN/LCSC fields.'
        elif ref in unresolved:
            fields['Procurement status'] += ': ' + unresolved[ref]
        c['procurement_fields'] = fields
    data['procurement_handoff'] = {
        'date': snapshot['date'], 'boards': 1000,
        'pricing_worksheet': '../references/pricing-1000pcs-2026-09-11.md',
        'bom': 'review/engineering-bom.csv', 'status': 'Engineering BOM; unresolved sourcing and footprint decisions remain',
        'priced_subset_inr': 231.2064, 'holder_allowance_inr': 30,
        'priced_subset_plus_holder_inr': 261.2064}


def annotate_schematic(path, data):
    tree = parse(path.read_text())
    baseline = copy.deepcopy(tree)
    comps = {c['ref']: c for c in data['components']}
    touched = 0
    for sym in children(tree, 'symbol'):
        props = {val(p[1]): p for p in children(sym, 'property')}
        c = comps.get(val(props['Reference'][2]))
        if not c or 'procurement_fields' not in c:
            continue
        fields = dict(c['procurement_fields'])
        fields.update({'Value': c['value'], 'MPN': c.get('mpn', ''),
                       'Manufacturer': c.get('manufacturer', ''), 'LCSC': c.get('lcsc', ''),
                       'Assembly note': c.get('note', '')})
        for name, value in fields.items():
            if name in props:
                props[name][2] = q(value)
            else:
                at = child(sym, 'at')
                sym.append(parse('(property '+q(name)+' '+q(value)+' (at '+at[1]+' '+at[2]+
                                 ' 0) (effects (font (size 1.27 1.27)) (hide yes)))'))
        touched += 1
    def circuitry(t):
        t = copy.deepcopy(t)
        for sym in children(t, 'symbol'):
            sym[:] = [x for x in sym if not (isinstance(x, list) and x[0] == 'property')]
        return t
    assert circuitry(tree) == circuitry(baseline), 'Unexpected circuit/layout modification'
    path.write_text(ser(tree) + '\n')
    return touched


def export_bom(folder):
    sch = folder / 'AQI_Battery_Cost_Revision.kicad_sch'
    fields = ['Reference', 'Value', 'MPN', 'Manufacturer', 'LCSC', 'Footprint', 'DNP',
              'Procurement status', 'Candidate MPN', 'Candidate LCSC', 'Candidate Manufacturer',
              'Budget USD each', 'Budget INR each', 'Price basis', 'Price source', 'Price date',
              'Catalogue stock', 'Assembly note']
    subprocess.run([CLI, 'sch', 'export', 'bom', '--fields', ','.join(fields),
                    '--labels', ','.join(fields), '--filter', '[!#]*',
                    '-o', str(folder / 'review/engineering-bom.csv'), str(sch)], check=True)


if __name__ == '__main__':
    folder = ROOT / 'cost-revision'
    path = folder / 'design.json'
    data = json.loads(path.read_text())
    before = copy.deepcopy(data)
    annotate_design(data)
    assert [(c['ref'], c['nets'], c.get('fp'), c.get('dnp')) for c in data['components']] == [
        (c['ref'], c['nets'], c.get('fp'), c.get('dnp')) for c in before['components']]
    path.write_text(json.dumps(data, indent=2) + '\n')
    count = annotate_schematic(folder / 'AQI_Battery_Cost_Revision.kicad_sch', data)
    export_bom(folder)
    print('Updated procurement fields on', count, 'components; circuitry and footprints preserved.')
