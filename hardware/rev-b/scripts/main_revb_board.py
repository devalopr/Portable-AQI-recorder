"""Rev B main PCB, stage 1: sync the routed Rev A copy to the Rev B netlist without losing routing.

Deletes removed footprints and the copper of nets that no longer exist, renames merged nets on the
existing copper, and adds the new footprints at the positions given in PLACE. Run with KiCad Python.
"""
from pathlib import Path
import json, sys
import xml.etree.ElementTree as ET
import pcbnew as pcb
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_common import Project, K

root = Path(__file__).resolve().parents[1] / 'main'
board_path = root / 'AQI_Main.kicad_pcb'
mm = pcb.FromMM
P = Project(root / 'design.json')
design = {c['ref']: c for c in P.comps if not c['ref'].startswith('#')}
PADNET = {}
for n in ET.parse(root / 'review/netlist.xml').getroot().iter('net'):
    for node in n.iter('node'):
        PADNET[(node.get('ref'), node.get('pin'))] = n.get('name')

RENAME = {'+5V_USB': '+5V_SYS', '/USB_LOCAL_D+': '/USB_D+', '/USB_LOCAL_D-': '/USB_D-',
          '/USB_SWITCH_D+': '/USB_D+', '/USB_SWITCH_D-': '/USB_D-', '/UART_TX': '/BAT_PWM_MCU'}
DEAD = {'+5V_INT', '/USB_INT_D+', '/USB_INT_D-', '/INT_HOST_PRESENT', '/USB_SEL_INT', '/USB_OE_N',
        '/PWR_PR1', '/BUTTON_OK', '/BUTTON_LEFT', '/BUTTON_RIGHT', '/BL_FB'}
# New or re-footprinted parts: (x, y, rotation) in board coordinates. Headers/USB/switch are
# re-oriented precisely in stage 2; these are starting positions.
PLACE = {'J2': (32.7, 75.35, 90.0), 'J8': (38.9, 75.35, 90.0), 'D2': (40.3, 72.3, 0.0),
         'J1': (26.0, 76.5, 0.0), 'SW1': (8.0, 66.25, 0.0), 'SW2': (22.0, 66.25, 0.0),
         'SW3': (36.0, 66.25, 0.0), 'SW4': (42.55, 65.2, 90.0), 'U5': (11.8, 48.8, 90.0),
         'U6': (10.4, 23.4, 90.0),
         'Q1': (36.5, 12.5, 0.0), 'R28': (40.0, 17.5, 0.0), 'R33': (60.0, 60.0, 0.0),
         'R34': (60.0, 50.0, 90.0)}


def net(b, name):
    ni = b.FindNet(name)
    if ni is None:
        ni = pcb.NETINFO_ITEM(b, name)
        b.Add(ni)
    return ni


def main():
    b = pcb.LoadBoard(str(board_path))
    live = {f.GetReference(): f for f in b.GetFootprints()}
    # A footprint whose library footprint changed (GH J2 -> Dupont J2) is replaced, not edited.
    doomed = [f for ref, f in live.items()
              if ref not in design or f.GetFPIDAsString() != design[ref].get('fp', f.GetFPIDAsString())]
    dead_copper = [t for t in b.GetTracks() if t.GetNetname() in DEAD]
    for t in b.GetTracks():
        if t.GetNetname() in RENAME:
            t.SetNet(net(b, RENAME[t.GetNetname()]))

    for ref, c in design.items():
        f = live.get(ref)
        if (f is None or f in doomed) and c.get('fp'):
            lib, name = c['fp'].split(':')
            f = pcb.FootprintLoad(str(root / 'lib/AQI.pretty') if lib == 'AQI' else str(K / 'footprints' / f'{lib}.pretty'), name)
            f.SetReference(ref); f.SetValue(c['value']); f.SetFPID(pcb.LIB_ID(lib, name))
            f.SetPath(pcb.KIID_PATH('/' + P.root + '/' + c['uuid']))
            x, y, rot = PLACE[ref]
            f.SetPosition(pcb.VECTOR2I(mm(x), mm(y)))
            f.Reference().SetLayer(pcb.F_Fab); f.Reference().SetTextSize(pcb.VECTOR2I(mm(.7), mm(.7)))
            f.Reference().SetTextThickness(mm(.12)); f.Value().SetVisible(False)
            b.Add(f)
            if c.get('side') == 'back':
                f.Flip(f.GetPosition(), False); f.Reference().SetLayer(pcb.B_Fab)
            f.SetOrientationDegrees(rot)
        if f is None:
            continue
        f.SetValue(c['value'])
        f.SetDNP(bool(c.get('dnp')))
        f.SetField('Datasheet', c.get('datasheet', ''))
        for name, key in [('MPN', 'mpn'), ('Manufacturer', 'manufacturer'), ('LCSC', 'lcsc'), ('Assembly note', 'note')]:
            new = not f.HasField(name)
            f.SetField(name, c.get(key, ''))
            if new:
                f.GetField(name).SetVisible(False)
        for pad in f.Pads():
            n = PADNET.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(net(b, n))
            elif pad.GetNumber():
                pad.SetNet(b.FindNet(''))
    names = sorted(f.GetReference() for f in doomed)
    for item in doomed + dead_copper:
        b.Delete(item)
    pcb.SaveBoard(str(board_path), b)
    print('synced; removed', names, len(dead_copper), 'dead tracks/vias')


if __name__ == '__main__':
    main()
