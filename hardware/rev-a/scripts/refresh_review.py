#!/usr/bin/env python3
"""Check/export authoritative KiCad files without rebuilding their routing.

Requires KiCad 10 CLI and a Python interpreter with pcbnew for the independent
pin audit. Use --render for native 3D previews (requires a graphics session).
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cli', default='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
parser.add_argument('--pcb-python', default='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9')
parser.add_argument('--render', action='store_true')
args = parser.parse_args()

def run(command, log):
    result = subprocess.run([str(x) for x in command], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    log.write_text(result.stdout)
    if result.returncode:
        raise RuntimeError('Command failed; see ' + str(log) + '\n' + result.stdout[-3000:])

manifest = {
    'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status': 'engineering_review_only',
    'fabrication_released': False,
    'kicad_version': subprocess.check_output([args.cli, 'version'], text=True).strip(),
    'scope': 'ERC/DRC under project rules, schematic parity and design pin comparison; no hardware or enclosure qualification.',
    'boards': {},
}
# Invalidate any old passing manifest before starting a new run.
(ROOT / 'validation.json').unlink(missing_ok=True)
for folder, name in [('main', 'AQI_Main'), ('battery', 'AQI_Battery')]:
    base = ROOT / folder
    review = base / 'review'
    review.mkdir(exist_ok=True)
    sch = base / (name + '.kicad_sch')
    pcb = base / (name + '.kicad_pcb')
    print('Checking ' + name, flush=True)
    for kind, source, extra in [('sch', sch, []), ('pcb', pcb, ['--refill-zones', '--schematic-parity'])]:
        check = 'erc' if kind == 'sch' else 'drc'
        run([args.cli, kind, check, '--format', 'json', '--exit-code-violations',
             '--output', review / (check + '.json'), *extra, source], review / (check + '.log'))
    run([args.cli, 'sch', 'export', 'netlist', '--format', 'kicadxml', '--output',
         review / 'netlist.xml', sch], review / 'netlist.log')
    run([args.pcb_python, ROOT / 'scripts/verify_connectivity.py', base], review / 'connectivity.log')
    run([args.cli, 'sch', 'export', 'pdf', '--output', review / (name + '.pdf'), sch], review / 'pdf.log')
    run([args.cli, 'sch', 'export', 'svg', '--output', review, sch], review / 'svg.log')
    fields = 'Reference,Value,MPN,Manufacturer,Footprint,DNP,Datasheet,Assembly note'
    run([args.cli, 'sch', 'export', 'bom', '--output', review / 'engineering-bom.csv',
         '--fields', fields, '--labels', fields, '--sort-field', 'Reference', sch], review / 'bom.log')
    for side, layers in [('front', 'F.Cu,F.SilkS,F.Fab,Edge.Cuts'),
                         ('rear', 'B.Cu,B.SilkS,B.Fab,Edge.Cuts')]:
        run([args.cli, 'pcb', 'export', 'svg', '--mode-single', '--page-size-mode', '2',
             '--layers', layers, *(['--mirror'] if side == 'rear' else []),
             '--output', review / (folder + '-' + side + '-layout.svg'), pcb], review / (side + '-svg.log'))
        if args.render:
            run([args.cli, 'pcb', 'render', '--output', review / (folder + '-' + side + '.png'),
                 '--width', '900', '--height', '1500', '--quality', 'basic', '--background', 'opaque',
                 '--side', 'top' if side == 'front' else 'bottom', pcb], review / (side + '-render.log'))
    erc = json.loads((review / 'erc.json').read_text())
    drc = json.loads((review / 'drc.json').read_text())
    connectivity = json.loads((review / 'connectivity.json').read_text())
    project = json.loads((base / (name + '.kicad_pro')).read_text())
    manifest['boards'][folder] = {
        'erc_violations': sum(len(s['violations']) for s in erc['sheets']),
        'drc_violations': len(drc['violations']),
        'unconnected_items': len(drc['unconnected_items']),
        'schematic_parity_issues': len(drc['schematic_parity']),
        'connected_pins_checked': connectivity['connected_pins_checked'],
        'connectivity_issues': connectivity['issues'],
        'erc_ignored_checks': erc.get('ignored_checks', []),
        'drc_ignored_checks': drc.get('ignored_checks', []),
        'drc_exclusions': project.get('board', {}).get('design_settings', {}).get('drc_exclusions', []),
        'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                   [sch, pcb, base / (name + '.kicad_pro'), base / 'design.json']},
    }
    print('Passed ' + name + ': ERC, DRC, parity and pin audit; exported review files.', flush=True)
(ROOT / 'validation.json').write_text(json.dumps(manifest, indent=2) + '\n')
