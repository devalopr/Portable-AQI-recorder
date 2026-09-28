"""Rev B main board, 2-layer / 76 mm re-layout (run with KiCad's Python).

Starts from the frozen 4-layer, 80 mm board in review/rev-b-4layer-80mm/ (its placement is the reference),
then:
  place   - strip all copper and the inner layers, cut the outline to 76 mm, move the bottom-edge parts up 4 mm
            and the SEN5x/SEN6x connectors 6 mm in from the right edge; write the board and a Specctra DSN.
  import  - read the Freerouting session (review/routing/AQI_Main.ses) into the placed board.
Ground pours, stitching and checks follow in main_revb_2layer_finish.py.

  export  - re-export the routed board so Freerouting can finish what the first pass left.
  sync    - write final part positions into design.json.
Usage: main_revb_2layer.py place | export | import | fields | sync
"""
from pathlib import Path
import json, re, shutil, sys
import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pcb_edit import V, move, via, orient_to

ROOT = Path(__file__).resolve().parents[1] / 'main'
BASE = ROOT / 'review/rev-b-4layer-80mm/AQI_Main.kicad_pcb'
BOARD = ROOT / 'AQI_Main.kicad_pcb'
ROUTE = ROOT / 'review/routing'
CUT = 4.0                                   # board length 80 -> 76 mm
SENSOR_SHIFT = 6.0                          # J3/J4 toward the centre (cable bend room)
WIDEN = 1.5                                 # extra board width per side (44 -> 47 mm); the outer 1 mm is a lip
LIP = 1.0
ISLAND_DY = -25.0   # CO2 island at the top of the right column (y 21-35), fed through its bottom-right tab


def fp(b, ref):
    return next(f for f in b.GetFootprints() if f.GetReference() == ref)


def shift(b, refs, dx=0.0, dy=0.0):
    for r in refs:
        f = fp(b, r)
        f.Move(V(dx, dy))


def sync_nets(b):
    """Apply the current schematic netlist to the pads (the 4-layer baseline predates later pin changes)."""
    import xml.etree.ElementTree as ET
    padnet = {}
    for n in ET.parse(ROOT / 'review/netlist.xml').getroot().iter('net'):
        for node in n.iter('node'):
            padnet[(node.get('ref'), node.get('pin'))] = n.get('name')
    changed = 0
    for f in b.GetFootprints():
        for p in f.Pads():
            want = padnet.get((f.GetReference(), p.GetNumber()))
            if want and p.GetNetname() != want:
                ni = b.FindNet(want)
                if ni is None:
                    ni = pcb.NETINFO_ITEM(b, want); b.Add(ni)
                p.SetNet(ni); changed += 1
    print('netlist sync:', changed, 'pads')


def strip(b):
    """Remove every track and via, the inner-layer zones and rule areas, then drop to two copper layers."""
    for t in list(b.GetTracks()):
        b.Delete(t)
    for z in list(b.Zones()):
        if not (z.IsOnLayer(pcb.F_Cu) or z.IsOnLayer(pcb.B_Cu)):
            b.Delete(z)
    b.SetCopperLayerCount(2)
    ds = b.GetDesignSettings()
    ds.SetCopperLayerCount(2)


def rule_area(b, name, x0, y0, x1, y1, tracks=True, vias=True, pour=False, layers=(pcb.F_Cu, pcb.B_Cu)):
    z = pcb.ZONE(b)
    z.SetIsRuleArea(True); z.SetZoneName(name)
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias); z.SetDoNotAllowZoneFills(pour)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcb.LSET()
    for l in layers:
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        o.Append(pcb.FromMM(x), pcb.FromMM(y))
    b.Add(z)
    return z


def widen(b):
    """Board 1.5 mm wider on each side (x -1.5 .. 45.5; coordinates of everything else unchanged). The outer 1 mm
    of each side is a mounting lip: no tracks or vias (ground pour only). Beside the CO2 island the new strip is
    kept copper-free so the island stays thermally isolated. SW4 moves out so its actuator still clears the edge."""
    if not WIDEN:
        return
    w = pcb.FromMM(WIDEN)
    for d in b.GetDrawings():
        if d.GetLayer() != pcb.Edge_Cuts:
            continue
        pts = (d.GetStart(), d.GetEnd())
        outer = any(abs(pcb.ToMM(q.y)) < 0.01 or abs(pcb.ToMM(q.y) - (80 - CUT)) < 0.01 or abs(pcb.ToMM(q.x)) < 0.01
                    or abs(pcb.ToMM(q.x) - 44) < 0.01 for q in pts)
        if not outer:
            continue
        def mv(q):
            x = pcb.ToMM(q.x)
            return pcb.VECTOR2I(q.x - w if x <= 1.51 else q.x + w if x >= 42.49 else q.x, q.y)
        d.SetStart(mv(pts[0])); d.SetEnd(mv(pts[1]))
    for z in b.Zones():
        poly = z.Outline()
        for i in range(poly.TotalVertices()):
            v = poly.CVertex(i); x = pcb.ToMM(v.x)
            if not z.GetIsRuleArea() and (x < 0.5 or x > 43.5):                 # GND pours to the new edges
                poly.SetVertex(i, pcb.VECTOR2I(v.x - w if x < 0.5 else v.x + w, v.y))
            elif z.GetIsRuleArea() and (x < 0.01 or x > 43.99):                 # antenna / tab keepouts
                poly.SetVertex(i, pcb.VECTOR2I(v.x - w if x < 0.01 else v.x + w, v.y))
    H = 80 - CUT
    rule_area(b, 'lip-left', -WIDEN, 0, -WIDEN + LIP, H)
    rule_area(b, 'lip-right', 44 + WIDEN - LIP, 0, 44 + WIDEN, H)
    iy0, iy1 = 46 + ISLAND_DY, 60 + ISLAND_DY
    rule_area(b, 'island-edge', 44, iy0 - 0.2, 44 + WIDEN, iy1 + 0.2, pour=True)
    shift(b, ['SW4'], dx=WIDEN)


def outline(b):
    """Pull the bottom edge, its chamfers, the antenna keepouts and the GND pour outlines up by CUT."""
    for d in b.GetDrawings():
        if d.GetLayer() == pcb.Edge_Cuts:
            for get, put in ((d.GetStart, d.SetStart), (d.GetEnd, d.SetEnd)):
                p = get()
                if pcb.ToMM(p.y) > 78.0:
                    put(pcb.VECTOR2I(p.x, p.y - pcb.FromMM(CUT)))
    for z in b.Zones():
        poly = z.Outline()
        bb = z.GetBoundingBox()
        if z.GetIsRuleArea() and pcb.ToMM(bb.GetY()) > 70:          # antenna keepout: move with the module
            z.Move(V(0, -CUT))
        elif not z.GetIsRuleArea():                                    # GND pours: bottom vertices up
            for i in range(poly.TotalVertices()):
                v = poly.CVertex(i)
                if pcb.ToMM(v.y) > 78.0:
                    poly.SetVertex(i, pcb.VECTOR2I(v.x, v.y - pcb.FromMM(CUT)))


def island_tab_routes(b):
    """Island fed through its bottom-right tab (x 41.5-44, y 34-35). U8 is turned so SDA/SCL/VDD/GND (pins 10, 9,
    7, 6) face the island's free right side. Tab lanes: back SDA x 42.3 and GND x 43.2, front VDD x 42.3 and SCL
    x 43.2. Under the island a channel (y 35.4-36.9) takes VDD west to U7 and SDA/SCL down to J3's I2C pins;
    VDDH (pin 19, far side) comes over the front from a via in the island's free top-left corner."""
    F, B = pcb.F_Cu, pcb.B_Cu
    fixed = [
        # inside the island (back)
        ('/I2C_SDA', B, 0.2, [(37.46, 30.5), (42.3, 30.5), (42.3, 36.5), (33.8, 36.5), (33.8, 42.0), (33.42, 42.38),
                              (32.42, 42.38)]),
        ('/I2C_SCL', B, 0.2, [(37.46, 29.25), (43.2, 29.25)]),
        ('/I2C_SCL', F, 0.2, [(43.2, 29.25), (43.2, 36.25), (33.8, 36.25), (33.8, 43.62)]),
        ('/I2C_SCL', B, 0.2, [(33.8, 43.62), (32.42, 43.62)]),
        ('+3V3_CO2', B, 0.25, [(37.46, 26.75), (40.2, 26.75)]),                      # VDD pin 7 to its via
        ('+3V3_CO2', B, 0.25, [(29.16, 26.75), (27.75, 26.75), (27.75, 24.3), (28.9, 23.8)]),   # VDDH pin 19
        ('+3V3_CO2', F, 0.25, [(28.9, 23.8), (39.4, 23.8), (40.2, 24.6), (40.2, 26.75), (42.3, 28.85),
                               (42.3, 35.75), (26.16, 35.75), (26.16, 36.5)]),
        ('+3V3_CO2', B, 0.3, [(26.16, 36.5), (26.16, 37.35)]),                      # U7 OUT (pin 5)
        ('GND', B, 0.4, [(43.2, 31.0), (43.2, 38.5)]),                             # island ground across the tab
    ]
    for net, layer, w, pts in fixed:
        for p0, p1 in zip(pts, pts[1:]):
            t = pcb.PCB_TRACK(b)
            t.SetStart(V(*p0)); t.SetEnd(V(*p1)); t.SetWidth(pcb.FromMM(w)); t.SetLayer(layer)
            t.SetNet(b.FindNet(net)); t.SetLocked(True); b.Add(t)
    for net, x, y in [('/I2C_SCL', 43.2, 29.25), ('/I2C_SCL', 33.8, 43.62), ('+3V3_CO2', 40.2, 26.75),
                      ('+3V3_CO2', 28.9, 23.8), ('+3V3_CO2', 26.16, 36.5)]:
        via(b, net, x, y).SetLocked(True)


def co2_bridge(b):
    """The CO2 island hangs on one 2 mm copper bridge (x 24-27, y 27-29 after the move; coordinates below are
    the island's original ones, shifted by ISLAND_DY). Keep routing 0.35 mm off the slot
    edges (copper-to-edge rule 0.3 mm) and pre-route the four nets that cross the bridge (the pour is not allowed
    on it, so the island's GND arrives as a track)."""
    m = 0.35
    slots = [(24, 54, 27, 60), (24, 59, 41.5 if ISLAND_DY else 42.5, 60), (24, 46, 27, 52), (24, 46, 42.5, 47)]
    for x0, y0, x1, y1 in slots:
        z = pcb.ZONE(b)
        z.SetIsRuleArea(True); z.SetZoneName('slot-margin')
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        ls = pcb.LSET(); ls.AddLayer(pcb.F_Cu); ls.AddLayer(pcb.B_Cu); z.SetLayerSet(ls)
        o = z.Outline(); o.NewOutline()
        y0, y1 = y0 + ISLAND_DY, y1 + ISLAND_DY
        for x, y in [(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)]:
            o.Append(pcb.FromMM(x), pcb.FromMM(y))
        b.Add(z)
    if ISLAND_DY:
        island_tab_routes(b)
        return
    # Fixed routes. Bridge (usable y 52.3-53.7): GND, +3V3_CO2 and SCL on the front, SDA on the back.
    # Inside the island U8 (SCD41 LGA) leaves only the via spots the 4-layer board used: SCL at (31.6, 55.9),
    # VDD/VDDH at (34.6, 58.3) / (34.6, 47.7), C16 at (41.6, 53.4). On the main side +3V3_CO2 runs over the
    # empty front to U7 and SCL drops to the back just west of the bridge, so the two never cross.
    F, B = pcb.F_Cu, pcb.B_Cu
    fixed = [
        ('GND', F, 0.25, [(23.2, 52.45), (27.8, 52.45)]),
        ('+3V3_CO2', F, 0.25, [(19.1, 55.4), (21.55, 52.95), (34.6, 52.95)]),
        ('+3V3_CO2', B, 0.3, [(19.86, 56.14), (19.1, 55.4)]),                      # U7 output (pin 5)
        ('+3V3_CO2', F, 0.25, [(34.6, 47.7), (34.6, 58.3)]),
        ('+3V3_CO2', F, 0.25, [(34.6, 53.4), (41.6, 53.4)]),
        ('+3V3_CO2', B, 0.25, [(34.6, 58.3), (34.56, 57.15)]),
        ('+3V3_CO2', B, 0.25, [(34.6, 47.7), (34.56, 48.85)]),
        ('+3V3_CO2', B, 0.25, [(41.6, 53.4), (42.45, 53.0)]),
        ('/I2C_SCL', F, 0.2, [(22.9, 54.3), (23.2, 53.45), (29.2, 53.45), (31.6, 55.85), (31.6, 55.9)]),
        ('/I2C_SCL', B, 0.15, [(31.6, 55.9), (31.8, 56.1), (31.8, 56.5), (32.06, 57.15)]),
        ('/I2C_SDA', B, 0.2, [(23.2, 53.0), (27.6, 53.0)]),
        ('/I2C_SDA', B, 0.15, [(27.6, 53.0), (27.7, 53.1), (27.7, 55.4), (27.9, 55.6), (27.9, 56.0), (28.1, 56.2),
                               (29.3, 56.2), (29.9, 56.8), (30.1, 56.8), (30.81, 57.15)]),
    ]
    for net, layer, w, pts in fixed:
        for a, z in zip(pts, pts[1:]):
            t = pcb.PCB_TRACK(b)
            t.SetStart(V(a[0], a[1] + ISLAND_DY)); t.SetEnd(V(z[0], z[1] + ISLAND_DY))
            t.SetWidth(pcb.FromMM(w)); t.SetLayer(layer); t.SetNet(b.FindNet(net)); t.SetLocked(True); b.Add(t)
    # GND: the bridge stub's front pour reaches the island back pour through the free corner above U8 pin 15.
    for net, x, y in [('GND', 28.9, 48.8), ('GND', 39.6, 49.6), ('GND', 39.6, 56.4),
                      ('/I2C_SCL', 31.6, 55.9), ('/I2C_SCL', 22.9, 54.3), ('+3V3_CO2', 19.1, 55.4), ('+3V3_CO2', 34.6, 58.3), ('+3V3_CO2', 34.6, 47.7),
                      ('+3V3_CO2', 41.6, 53.4)]:
        v = via(b, net, x, y + ISLAND_DY); v.SetLocked(True)


def display_bus(b):
    """Display SPI (DC, CS, SCK, MOSI, RST, in J5's order at both ends) is fixed before autorouting: a via just
    above each module pin, west on the front, up a 5-lane bus along the left edge, east along y 21.2-22.8 and
    down a via beside each J5 pad."""
    lanes = [('/DISP_DC', 7.4, 58.7, 1.0, 21.2, 18.5),        # net, pin x, row y (west run), lane x, top row y, J5 x
             ('/DISP_CS', 9.0, 57.95, 1.4, 21.6, 19.5),
             ('/DISP_SCK', 9.8, 57.55, 1.8, 22.0, 20.5),
             ('/DISP_MOSI', 10.6, 57.15, 2.2, 22.4, 21.5),
             ('/DISP_RST', 11.4, 56.75, 2.6, 22.8, 22.5)]
    for net, px, ry, lx, ty, jx in lanes:
        segs = [(pcb.B_Cu, [(px, 59.6), (px, 58.7)]),
                (pcb.F_Cu, [(px, 58.7), (px, ry), (lx, ry), (lx, ty), (jx, ty), (jx, 20.2)]),
                (pcb.B_Cu, [(jx, 20.2), (jx, 18.65)])]
        for layer, pts in segs:
            pts = [q for n, q in enumerate(pts) if n == 0 or q != pts[n - 1]]
            for p0, p1 in zip(pts, pts[1:]):
                t = pcb.PCB_TRACK(b)
                t.SetStart(V(*p0)); t.SetEnd(V(*p1)); t.SetWidth(pcb.FromMM(0.2)); t.SetLayer(layer)
                t.SetNet(b.FindNet(net)); t.SetLocked(True); b.Add(t)
        via(b, net, px, 58.7).SetLocked(True)
        via(b, net, jx, 20.2).SetLocked(True)             # just below J5's pads
    # Backlight PWM (module pin 6, far side) takes the outermost lane, south of the display rows at both ends;
    # the router finishes it from (3.0, 20.6) to the backlight FET.
    for layer, pts in [(pcb.B_Cu, [(3.1, 64.5), (3.9, 64.5), (4.7, 63.7)]),
                       (pcb.F_Cu, [(4.7, 63.7), (4.7, 60.0), (0.55, 60.0), (0.55, 20.6), (3.0, 20.6)])]:
        for p0, p1 in zip(pts, pts[1:]):
            t = pcb.PCB_TRACK(b)
            t.SetStart(V(*p0)); t.SetEnd(V(*p1)); t.SetWidth(pcb.FromMM(0.2)); t.SetLayer(layer)
            t.SetNet(b.FindNet('/BL_PWM')); t.SetLocked(True); b.Add(t)
    via(b, '/BL_PWM', 4.7, 63.7).SetLocked(True)
    # Button lines from the module's top edge: GPIO8 (pin 22) straight down the front to LEFT (SW1);
    # GPIO9 (pin 23) along the back past the module corner, then down the front to OK (SW2).
    for net, segs, vias in [
            ('/BOOT_GPIO8', [(pcb.B_Cu, [(12.2, 59.6), (12.2, 58.7)]),
                             (pcb.B_Cu, [(12.2, 58.7), (14.8, 56.1), (14.8, 55.925)]),          # pull-up R3
                             (pcb.F_Cu, [(12.2, 58.7), (12.2, 63.9), (12.0, 64.1), (12.0, 64.375)])], [(12.2, 58.7)]),
            ('/BOOT_GPIO9', [(pcb.B_Cu, [(13.0, 59.6), (13.0, 58.9), (17.3, 58.9)]),
                             (pcb.F_Cu, [(17.3, 58.9), (17.3, 63.5), (18.175, 64.375), (19.0, 64.375)])], [(17.3, 58.9)])]:
        for layer, pts in segs:
            for p0, p1 in zip(pts, pts[1:]):
                t = pcb.PCB_TRACK(b)
                t.SetStart(V(*p0)); t.SetEnd(V(*p1)); t.SetWidth(pcb.FromMM(0.2)); t.SetLayer(layer)
                t.SetNet(b.FindNet(net)); t.SetLocked(True); b.Add(t)
        for x, y in vias:
            via(b, net, x, y).SetLocked(True)
    # U4 load-switch control lines to C8 (CT), R15 (ON) and R16 (QOD), and D1's ground to the USB-C shield.
    for net, segs, vias in [
            # U4 (turned): CT east to C8, QOD down beside C8 to R16, ON under the slot corner to R15
            ('/MAIN_CT', [(pcb.B_Cu, [(22.14, 61.14), (24.9, 61.14), (25.525, 61.765), (25.525, 62.0)])], []),
            ('/MAIN_QOD', [(pcb.B_Cu, [(22.14, 62.09), (23.1, 62.09), (23.1, 64.9), (23.7, 65.5), (24.675, 65.5)])], []),
            ('/MAIN_ON', [(pcb.B_Cu, [(19.86, 61.14), (19.86, 60.45), (26.9, 60.45), (26.9, 63.2), (26.075, 63.75)])], []),
            ('GND', [(pcb.B_Cu, [(20.34, 73.05), (19.2, 73.05)]),
                     (pcb.F_Cu, [(19.2, 73.05), (21.35, 74.2), (22.38, 74.2)])], [(19.2, 73.05)])]:
        for layer, pts in segs:
            for p0, p1 in zip(pts, pts[1:]):
                t = pcb.PCB_TRACK(b)
                t.SetStart(V(*p0)); t.SetEnd(V(*p1)); t.SetLayer(layer); t.SetNet(b.FindNet(net))
                t.SetWidth(pcb.FromMM(0.3 if net == 'GND' else 0.2)); t.SetLocked(True); b.Add(t)
        for x, y in vias:
            via(b, net, x, y).SetLocked(True)
    # USB pair from module pins 26 (D-) / 27 (D+) to R8 / R7, threading between C15 and the pin-30/31 vias.
    for net, pts in [('/USB_MCU_D-', [(14.9, 61.3), (16.2, 61.3), (16.2, 62.0), (17.9, 63.7), (18.1, 63.88)]),
                     ('/USB_MCU_D+', [(14.9, 62.1), (15.6, 62.1), (15.6, 62.6), (16.9, 63.9), (16.9, 65.9),
                                      (18.1, 67.08)])]:
        for p0, p1 in zip(pts, pts[1:]):
            t = pcb.PCB_TRACK(b)
            t.SetStart(V(*p0)); t.SetEnd(V(*p1)); t.SetWidth(pcb.FromMM(0.2)); t.SetLayer(pcb.B_Cu)
            t.SetNet(b.FindNet(net)); t.SetLocked(True); b.Add(t)
    # Battery PWM (GPIO21, module pin 31) across the bottom band: front lane y 65.45 between the button pad rows
    # and the GPIO2 line, back down before SW3's GPIO2 feed, then to R34.
    for layer, pts in [(pcb.B_Cu, [(14.9, 65.3), (16.3, 65.4)]),
                       (pcb.F_Cu, [(16.3, 65.4), (16.35, 65.45), (30.2, 65.45)]),
                       (pcb.B_Cu, [(30.2, 65.45), (34.2, 65.45), (34.675, 65.9)])]:
        for p0, p1 in zip(pts, pts[1:]):
            t = pcb.PCB_TRACK(b)
            t.SetStart(V(*p0)); t.SetEnd(V(*p1)); t.SetWidth(pcb.FromMM(0.2)); t.SetLayer(layer)
            t.SetNet(b.FindNet('/BAT_PWM_MCU')); t.SetLocked(True); b.Add(t)
    via(b, '/BAT_PWM_MCU', 16.3, 65.4).SetLocked(True)
    via(b, '/BAT_PWM_MCU', 30.2, 65.45).SetLocked(True)
    # E-paper BUSY (module pin 30, right side) runs up the front just east of the solid ground strip to TP5.
    for layer, pts in [(pcb.B_Cu, [(14.9, 64.5), (16.3, 64.5)]),
                       (pcb.F_Cu, [(16.3, 64.5), (16.45, 64.35), (16.45, 37.2), (19.9, 35.75), (20.6, 35.75)]),
                       (pcb.B_Cu, [(20.6, 35.75), (21.75, 35.75)])]:
        for p0, p1 in zip(pts, pts[1:]):
            t = pcb.PCB_TRACK(b)
            t.SetStart(V(*p0)); t.SetEnd(V(*p1)); t.SetWidth(pcb.FromMM(0.2)); t.SetLayer(layer)
            t.SetNet(b.FindNet('/EPD_BUSY')); t.SetLocked(True); b.Add(t)
    via(b, '/EPD_BUSY', 16.3, 64.5).SetLocked(True)
    via(b, '/EPD_BUSY', 20.6, 35.75).SetLocked(True)


def gnd_fanout(b):
    """Before routing, give every ground pad its own via to the front plane (0.3 mm stub, fixed), so the router
    has to leave room for it and no ground pad ends up boxed in by signal tracks."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ground import Stitcher
    st = Stitcher(b, excl_boxes=[], pour_layers=(), margin=0.0, pad_gap=0.2, via_gap=0.3, gnd_pad_gap=0.05)
    n = 0
    for f in b.GetFootprints():
        if f.IsBoardOnly():
            continue
        for pad in f.Pads():
            if pad.GetNetname() != 'GND' or pad.GetDrillSize().x > 0 or not pad.IsOnLayer(pcb.B_Cu):
                continue
            q = pad.GetPosition(); x, y = pcb.ToMM(q.x), pcb.ToMM(q.y)
            spot = st.near(x, y, rmin=0.55, rmax=1.3, have=1.1, step=0.05)
            if spot:
                t = pcb.PCB_TRACK(b)
                t.SetStart(q); t.SetEnd(V(*spot)); t.SetWidth(pcb.FromMM(0.3)); t.SetLayer(pcb.B_Cu)
                t.SetNet(b.FindNet('GND')); t.SetLocked(True); b.Add(t)
                n += 1
    for t in b.GetTracks():
        if t.Type() == pcb.PCB_VIA_T and t.GetNetname() == 'GND':
            t.SetLocked(True)
    print('gnd fanout:', n, 'pad vias')


def ground_neck(b):
    """The CO2 island slots cut the right half of the band y 21-35, so every ground return between the top and
    bottom of the board passes through the 24 mm neck on the left (below the display bus rows at y 21-23). Keep the front copper there free of signal
    tracks (vias allowed) so the front pour stays one continuous plane through the neck."""
    z = pcb.ZONE(b)
    z.SetIsRuleArea(True); z.SetZoneName('front-ground-neck')
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(False)
    z.SetDoNotAllowZoneFills(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcb.LSET(); ls.AddLayer(pcb.F_Cu); z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    y0, y1 = (23.3, 35.5) if ISLAND_DY else (42.0, 56.5)               # beside the island, clear of the display rows
    for x, y in [(8.5, y0), (16.0, y0), (16.0, y1), (8.5, y1)]:        # signal lanes either side
        o.Append(pcb.FromMM(x), pcb.FromMM(y))
    b.Add(z)


def buttons_route(b):
    """RIGHT button (GPIO2, module pin 5 on the far side) is fixed before autorouting: out of pin 5 on the back
    into the lane between the module's left pins and its centre ground pads, up a via, then along the front
    between the button pad rows (y 66.25, under the button bodies) to SW3."""
    for layer, pts in [(pcb.B_Cu, [(3.1, 65.3), (4.7, 65.3)]),
                       (pcb.F_Cu, [(4.7, 65.3), (5.65, 66.25), (30.9, 66.25), (32.0, 65.15), (32.0, 64.375)])]:
        for p0, p1 in zip(pts, pts[1:]):
            t = pcb.PCB_TRACK(b)
            t.SetStart(V(*p0)); t.SetEnd(V(*p1)); t.SetWidth(pcb.FromMM(0.2)); t.SetLayer(layer)
            t.SetNet(b.FindNet('/BOOT_GPIO2')); t.SetLocked(True); b.Add(t)
    via(b, '/BOOT_GPIO2', 4.7, 65.3).SetLocked(True)


def straight_headers(b):
    """J2 (battery PWM) and J8 (external 5 V, DNP) become straight 2.54 mm headers on the back, pins in the same
    places as the right-angle ones (so routing is unaffected); the enclosure has room above the back."""
    from kicad_common import K
    for ref in ('J2', 'J8'):
        old = fp(b, ref)
        if 'Vertical' in str(old.GetFPID().GetLibItemName()):
            continue
        pins = {p.GetNumber(): p for p in old.Pads()}
        p1, p2 = pins['1'].GetPosition(), pins['2'].GetPosition()
        new = pcb.FootprintLoad(str(K / 'footprints' / 'Connector_PinHeader_2.54mm.pretty'),
                                'PinHeader_1x02_P2.54mm_Vertical')
        new.SetFPID(pcb.LIB_ID('Connector_PinHeader_2.54mm', 'PinHeader_1x02_P2.54mm_Vertical'))
        b.Add(new)
        new.Flip(new.GetPosition(), False)
        for rot in (0, 90, 180, 270):
            new.SetOrientationDegrees(rot)
            new.SetPosition(pcb.VECTOR2I(0, 0))
            q = {p.GetNumber(): p.GetPosition() for p in new.Pads()}
            d = q['2'] - q['1']
            if abs(d.x - (p2.x - p1.x)) < 1000 and abs(d.y - (p2.y - p1.y)) < 1000:
                new.SetPosition(p1 - q['1'])
                break
        comp = next(c for c in json.loads((ROOT / 'design.json').read_text())['components'] if c['ref'] == ref)
        new.SetReference(ref); new.SetValue(comp['value']); new.SetDNP(old.IsDNP())
        fields = {fld.GetName(): fld.GetText() for fld in old.GetFields()
                  if fld.GetName() not in ('Reference', 'Value', 'Footprint')}
        fields.update({'MPN': comp.get('mpn', ''), 'Manufacturer': comp.get('manufacturer', ''),
                       'LCSC': comp.get('lcsc', fields.get('LCSC', '')), 'Datasheet': comp.get('datasheet', '')})
        for name, text in fields.items():
            new.SetField(name, text)
            fld = next(f for f in new.GetFields() if f.GetName() == name)
            fld.SetVisible(False); fld.SetLayer(pcb.B_Fab)
        for p in new.Pads():
            p.SetNet(pins[p.GetNumber()].GetNet())
        new.Reference().SetLayer(old.Reference().GetLayer()); new.Reference().SetPosition(old.Reference().GetPosition())
        b.Delete(old)


def move_island(b):
    """CO2 island to the top of the right column (under J5), fed through its bottom-right tab: the slots, rule
    areas, U8 and C16 move by ISLAND_DY; the bottom slot ends 1 mm earlier so that tab is 2.5 mm wide and carries
    the island's copper; the left middle tab becomes mechanical only. U8 turns so its SDA/SCL/VDD/GND pins face
    the tab side. U7 (the CO2 LDO) moves beside J3's 5 V pin; J3/J4 drop to leave a channel under the island."""
    dy = pcb.FromMM(ISLAND_DY)
    for d in b.GetDrawings():
        if d.GetLayer() == pcb.Edge_Cuts:
            s0, e0 = d.GetStart(), d.GetEnd()
            if all(23.9 <= pcb.ToMM(q.x) <= 42.6 and 45.9 <= pcb.ToMM(q.y) <= 60.1 for q in (s0, e0)):
                s1, e1 = pcb.VECTOR2I(s0.x, s0.y + dy), pcb.VECTOR2I(e0.x, e0.y + dy)
                # bottom slot (y 59-60 before the move) ends at x 41.5 instead of 42.5: wider copper tab
                fix = lambda q: pcb.VECTOR2I(pcb.FromMM(41.5), q.y) if abs(pcb.ToMM(q.x) - 42.5) < 0.01 and \
                    pcb.ToMM(q.y) > 33.5 else q
                d.SetStart(fix(s1)); d.SetEnd(fix(e1))
    for z in list(b.Zones()):
        bb = z.GetBoundingBox()
        if z.GetIsRuleArea() and pcb.ToMM(bb.GetX()) > 23 and 45 < pcb.ToMM(bb.GetY()) < 61:
            z.Move(V(0, ISLAND_DY))
            bb = z.GetBoundingBox()
            if pcb.ToMM(bb.GetX()) > 42 and pcb.ToMM(bb.GetY()) > 33:          # bottom-right tab: copper allowed
                b.Delete(z)
            elif pcb.ToMM(bb.GetRight()) < 28:                                   # left tab: mechanical only
                z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowZoneFills(True)
    shift(b, ['U8', 'C16'], dy=ISLAND_DY)
    u8 = fp(b, 'U8'); c = u8.GetPosition()
    for rot in (0, 90, 180, 270):
        u8.SetOrientationDegrees(rot); u8.SetPosition(c)
        q = {p.GetNumber(): p.GetPosition() for p in u8.Pads()}
        if q['6'].x > c.x + pcb.FromMM(3) and q['10'].x > c.x + pcb.FromMM(3) and q['6'].y > q['10'].y:
            break
    move(b, 'U7', 27.3, 38.3)                       # CO2 LDO left of J3, next to its 5 V pin
    move(b, 'C42', 24.2, 37.35, 180)                # U7 output cap, +3V3_CO2 pad toward OUT
    move(b, 'C15', 27.3, 41.6)                      # U7 input cap below it
    # SCD41 supply cap off the island, below U7's output (7 mm from the sensor body, across the slot), so hot air
    # on the sensor when it is fitted later doesn't lift it. It also serves as U7's bulk output cap.
    orient_to(b, 'C16', 25.0, 42.0, {'1': (0, -1), '2': (0, 1)})
    # SEN5x then SEN6x below the island, mouths still 6.5 mm in from the right edge
    shift(b, ['J3'], dy=13.5)
    shift(b, ['J4'], dy=14.0)


EPD_X, EPD_Y = 5.0, 1.5                         # header centre line and pin 1: near the edge, clear of J5 for the iron
EPD_REMOVED = ['J7', 'R30', 'R31', 'R32', 'L3', 'Q3', 'D10', 'D11', 'D12', 'C30', 'C31', 'C32', 'C33', 'C34',
               'C35', 'C36', 'C38', 'C39', 'C40', 'C41']


def epd_header(b):
    """The on-board e-paper boost circuit and 24-pin FPC (J6) give way to an unfitted 1x8 2.54 mm header for an
    external adapter (DESPI-C02 pin order), standing on the back along the top-left edge, pin 1 at the top. The
    header is the SMD version: through-hole pins would leave bare pads under the TFT in the default build."""
    from kicad_common import K
    for r in EPD_REMOVED + ['J6']:
        b.Delete(fp(b, r))
    new = pcb.FootprintLoad(str(K / 'footprints' / 'Connector_PinHeader_2.54mm.pretty'),
                            'PinHeader_1x08_P2.54mm_Vertical_SMD_Pin1Left')
    new.SetFPID(pcb.LIB_ID('Connector_PinHeader_2.54mm', 'PinHeader_1x08_P2.54mm_Vertical_SMD_Pin1Left'))
    b.Add(new)
    new.Flip(new.GetPosition(), False)
    for rot in (0, 90, 180, 270):
        new.SetOrientationDegrees(rot)
        q = {p.GetNumber(): p.GetPosition() for p in new.Pads()}
        if q['8'].y > q['1'].y and abs(q['8'].x - q['1'].x) < pcb.FromMM(4):
            break
    mid = pcb.VECTOR2I((q['1'].x + q['2'].x) // 2, q['1'].y)
    new.SetPosition(new.GetPosition() + V(EPD_X, EPD_Y) - mid)
    comp = next(c for c in json.loads((ROOT / 'design.json').read_text())['components'] if c['ref'] == 'J6')
    new.SetReference('J6'); new.SetValue(comp['value']); new.SetDNP(True)
    for name, text in {'MPN': comp.get('mpn', ''), 'Manufacturer': comp.get('manufacturer', ''),
                       'LCSC': comp.get('lcsc', ''), 'Datasheet': '', 'Assembly note': comp.get('note', '')}.items():
        new.SetField(name, text)
        fld = next(f for f in new.GetFields() if f.GetName() == name)
        fld.SetVisible(False); fld.SetLayer(pcb.B_Fab)
    new.Value().SetVisible(False)
    for p in new.Pads():
        net = {'1': '/EPD_BUSY', '2': '/DISP_RST', '3': '/DISP_DC', '4': '/DISP_CS', '5': '/DISP_SCK',
               '6': '/DISP_MOSI', '7': 'GND', '8': '+3V2'}[p.GetNumber()]
        ni = b.FindNet(net)
        assert ni is not None, net
        p.SetNet(ni)
    # pin names beside each pad on the back silk, and the adapter name above the column
    x = EPD_X + 3.6
    for n, name in enumerate(['BUSY', 'RES', 'DC', 'CS', 'SCK', 'SDI', 'GND', '3V3']):
        t = pcb.PCB_TEXT(b)
        t.SetText(name); t.SetLayer(pcb.B_SilkS); t.SetMirrored(True)
        t.SetTextSize(V(0.8, 0.8)); t.SetTextThickness(pcb.FromMM(0.15))
        t.SetHorizJustify(pcb.GR_TEXT_H_ALIGN_RIGHT)          # mirrored: the text runs east from x (toward J5)
        t.SetPosition(V(x, EPD_Y + 2.54 * n))
        b.Add(t)
    new.Reference().SetLayer(pcb.B_SilkS); new.Reference().SetPosition(V(EPD_X, 21.3)); new.Reference().SetVisible(False)
    # R27 (backlight gate pull-down) leaves the header's corner for Q1, between its gate and source pins
    orient_to(b, 'R27', 35.2, 13.1, {'1': (0, 1), '2': (0, -1)})


def place(b):
    # ESP32 module and its supply caps move up with the edge; the antenna stays at the edge.
    shift(b, ['U1', 'C1', 'C2', 'C3'], dy=-CUT)
    # Parts that sat above the module move clear of it.
    shift(b, ['R1'], dy=-CUT)                       # EN pull-up
    shift(b, ['R2'], dy=-3.0)                       # GPIO9 pull-up
    move(b, 'R3', 14.8, 55.1)                       # GPIO8 pull-up, beside the module
    shift(b, ['C7'], dy=-1.5)                       # opens a fan-out band above the module's top pins
    move(b, 'TP2', 2.5, 47.3)                       # EN test pad, left edge (clear of the module's top pins)
    move(b, 'TP3', 2.5, 50.3)                       # BOOT test pad
    # USB-C: mouth on the new edge (origin 4.09 mm inside it); shield legs clear SW2's pads.
    move(b, 'J1', 26.7, 80.0 - CUT - 4.09)
    move(b, 'D1', 19.2, 73.05)
    move(b, 'R8', 18.1, 64.7)                       # D- series R on top, D+ below: same order as the module
    move(b, 'R7', 18.1, 67.9)                       # pins and D1, so the pair never crosses
    move(b, 'R6', 23.6, 67.6)                       # CC pull-downs, between the button row and J1
    move(b, 'R5', 29.9, 67.6)
    # Dupont headers keep their x; battery-PWM and external-5 V parts regroup above them.
    shift(b, ['J2', 'J8'], dy=-3.25)                # pin row 72.1: J8 clears SW4
    move(b, 'C15', 17.0, 60.7, 90)                  # CO2 LDO input cap (DNP), between the module and U4/U7
    # Load switch U4 and the (DNP) CO2 LDO U7 swap places: U4 turned 180 deg so CT/QOD face C8/R16 and ON can
    # run under the slot corner; U7 sits beside the CO2 bridge, which also shortens its output run.
    u4, u7 = fp(b, 'U4'), fp(b, 'U7')
    p4, p7 = u4.GetPosition(), u7.GetPosition()
    u4.SetOrientationDegrees(u4.GetOrientationDegrees() + 180); u4.SetPosition(p7)
    u7.SetPosition(p4)
    move(b, 'C42', 20.2, 59.35)                     # U7 output cap (DNP) between the two
    move(b, 'D2', 37.0, 67.9)
    move(b, 'R34', 35.5, 65.9)
    move(b, 'R33', 35.5, 64.2)
    move(b, 'TP4', 37.9, 62.4)
    # Sensor connectors toward the centre so the cable can bend down inside the case.
    shift(b, ['J3', 'J4'], dx=-SENSOR_SHIFT)
    if ISLAND_DY:
        move_island(b)
    straight_headers(b)
    epd_header(b)
    # Button labels sit left of centre so "OK" clears J1's shield slot.
    for t in b.GetDrawings():
        if t.GetClass() == 'PCB_TEXT' and t.GetLayer() == pcb.F_SilkS and t.GetText() in ('L', 'OK', 'R'):
            t.Move(V(-1.4, 0))


# Freerouting: route mainly on the back (component side) so the front stays a near-solid ground plane.
AUTOROUTE = """
    (autoroute_settings
      (fanout off) (autoroute on) (postroute on) (vias on)
      (via_costs 40) (plane_via_costs 5) (start_ripup_costs 100) (start_pass_no 1)
      (layer_rule F.Cu (active on) (preferred_direction horizontal)
        (preferred_direction_trace_costs 3.0) (against_preferred_direction_trace_costs 4.0))
      (layer_rule B.Cu (active on) (preferred_direction vertical)
        (preferred_direction_trace_costs 1.0) (against_preferred_direction_trace_costs 1.6))
    )"""


def save_fixed(b):
    """Remember the pre-routes: a Specctra session import recreates every track unlocked."""
    fixed = {'tracks': [], 'vias': []}
    for t in b.GetTracks():
        if not t.IsLocked():
            continue
        if t.Type() == pcb.PCB_VIA_T:
            fixed['vias'].append([t.GetNetname(), t.GetPosition().x, t.GetPosition().y])
        else:
            fixed['tracks'].append([t.GetNetname(), t.GetLayer(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y])
    (ROUTE / 'fixed.json').write_text(json.dumps(fixed))


def relock(b):
    fixed = json.loads((ROUTE / 'fixed.json').read_text())
    segs = {(n, l, min((sx, sy), (ex, ey)), max((sx, sy), (ex, ey))) for n, l, sx, sy, ex, ey in fixed['tracks']}
    vias = {(n, x, y) for n, x, y in fixed['vias']}
    n = 0
    for t in b.GetTracks():
        if t.Type() == pcb.PCB_VIA_T:
            key = (t.GetNetname(), t.GetPosition().x, t.GetPosition().y)
            hit = key in vias
        else:
            a, z = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
            hit = (t.GetNetname(), t.GetLayer(), min(a, z), max(a, z)) in segs
        if hit:
            t.SetLocked(True); n += 1
    print(f'relocked {n} of {len(segs) + len(vias)} pre-routed items')


def export_dsn(b):
    ROUTE.mkdir(parents=True, exist_ok=True)
    dsn = ROUTE / 'AQI_Main.dsn'
    assert pcb.ExportSpecctraDSN(b, str(dsn))
    s = dsn.read_text()
    # The bridge's rule area only forbids pours; do not let it block tracks in the router.
    ky = int(-(51.5 + ISLAND_DY) * 1000) if not ISLAND_DY else 999999   # (tab variant: left tab stays blocked)
    s = re.sub(r'\(keepout "" \(polygon [FB]\.Cu 0  23500 %d[^)]*?\)\)\n?' % ky, '', s, flags=re.S)
    i = s.index('(boundary')                        # after the layer definitions
    s = s[:i] + AUTOROUTE.strip() + '\n    ' + s[i:]
    dsn.write_text(s)
    print('wrote', dsn)


def sync_design(b):
    path = ROOT / 'design.json'
    d = json.loads(path.read_text())
    live = {f.GetReference(): f for f in b.GetFootprints()}
    for c in d['components']:
        f = live.get(c['ref'])
        if f is not None:
            c['xy'] = [round(pcb.ToMM(f.GetPosition().x), 4), round(pcb.ToMM(f.GetPosition().y), 4)]
            c['rot'] = round(f.GetOrientationDegrees(), 3)
            c['side'] = 'back' if f.IsFlipped() else 'front'
    d['copper_layers'] = 2
    path.write_text(json.dumps(d, indent=2) + '\n')


def sync_fields(b):
    """Fitted/unfitted state and the MPN, Manufacturer, LCSC and Assembly note fields follow design.json (the 4-layer
    baseline predates later population changes). New fields are hidden on B.Fab."""
    comps = {c['ref']: c for c in json.loads((ROOT / 'design.json').read_text())['components']}
    for f in b.GetFootprints():
        c = comps.get(f.GetReference())
        if c is None:
            continue
        f.SetDNP(bool(c.get('dnp')))
        have = {fld.GetName(): fld for fld in f.GetFields()}
        for name, key in [('MPN', 'mpn'), ('Manufacturer', 'manufacturer'), ('LCSC', 'lcsc'), ('Assembly note', 'note')]:
            text = c.get(key) or ''
            if name in have:
                if have[name].GetText() != text:
                    have[name].SetText(text)
            elif text:
                f.SetField(name, text)
                fld = next(x for x in f.GetFields() if x.GetName() == name)
                fld.SetVisible(False); fld.SetLayer(pcb.B_Fab)


def main(mode):
    if mode == 'place':
        shutil.copy(BASE, BOARD)
        b = pcb.LoadBoard(str(BOARD))
        strip(b)
        sync_nets(b)
        outline(b)
        widen(b)
        place(b)
        co2_bridge(b)
        buttons_route(b)
        ground_neck(b)
        display_bus(b)
        gnd_fanout(b)
        sync_fields(b)
        pcb.SaveBoard(str(BOARD), b)
        b = pcb.LoadBoard(str(BOARD))
        ROUTE.mkdir(parents=True, exist_ok=True)
        save_fixed(b)
        export_dsn(b)
        sync_design(b)
    elif mode == 'headers':                         # apply the straight-header swap to the current board
        b = pcb.LoadBoard(str(BOARD)); straight_headers(b); pcb.SaveBoard(str(BOARD), b)
    elif mode == 'fields':                          # apply design.json population/part fields to the board
        b = pcb.LoadBoard(str(BOARD)); sync_fields(b); pcb.SaveBoard(str(BOARD), b)
    elif mode == 'sync':                            # record final positions (after the touch-up)
        sync_design(pcb.LoadBoard(str(BOARD)))
    elif mode == 'export':                          # re-export the routed board for another router pass
        export_dsn(pcb.LoadBoard(str(BOARD)))
    elif mode == 'import':
        b = pcb.LoadBoard(str(BOARD))
        ses = ROUTE / 'AQI_Main.ses'
        assert ses.stat().st_size > 1000, 'empty router output'
        assert pcb.ImportSpecctraSES(b, str(ses))
        relock(b)
        pcb.SaveBoard(str(BOARD), b)
        print('imported', ses)


if __name__ == '__main__':
    main(sys.argv[1])
