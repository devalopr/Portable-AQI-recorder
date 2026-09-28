"""Ground-plane helpers for the Rev B main board: inner-layer swap and GND stitching vias."""
import math
import pcbnew as pcb
from pcb_edit import via, V

mm, tomm = pcb.FromMM, pcb.ToMM
CU = [pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.B_Cu]


def swap_inner_routing(b):
    """Move all In2 routing to In1 so In2 (next to the component side, B.Cu) is an unbroken GND plane."""
    n = 0
    for t in b.GetTracks():
        if t.Type() != pcb.PCB_VIA_T and t.GetLayer() == pcb.In2_Cu:
            t.SetLayer(pcb.In1_Cu); n += 1
    return n


class Stitcher:
    """Places GND vias only where every copper layer is already GND pour with margin, away from
    pads, holes and existing vias; so a new via can never create a clearance or connectivity error."""

    def __init__(self, b, excl_boxes=(), margin=0.2, pad_gap=0.25, via_gap=0.45, pour_layers=(pcb.B_Cu, pcb.In2_Cu),
                 gnd_pad_gap=None):
        self.b = b
        self.gnd_pad_gap = pad_gap if gnd_pad_gap is None else gnd_pad_gap
        self.pour_layers = pour_layers
        self.gnd = b.FindNet('GND').GetNetCode()
        self.zones = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetCode() == self.gnd]
        self.rules = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]   # via keepouts only
        self.pads = [(p, self._box(p.GetBoundingBox())) for f in b.GetFootprints() for p in f.Pads()]
        self.holes = [(p.GetPosition(), tomm(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2)
                      for p, _ in self.pads if p.GetDrillSize().x > 0]
        self.vias = [(tomm(t.GetPosition().x), tomm(t.GetPosition().y)) for t in b.GetTracks()
                     if t.Type() == pcb.PCB_VIA_T]
        self.tracks = [(t, self._box(t.GetBoundingBox())) for t in b.GetTracks()
                       if t.Type() != pcb.PCB_VIA_T and t.GetNetCode() != self.gnd]
        self.excl = list(excl_boxes)
        self.r = 0.3 + margin          # via copper radius plus extra margin inside the pour
        self.pad_gap, self.via_gap = pad_gap, via_gap
        self.added = []

    @staticmethod
    def _box(bb):
        return (tomm(bb.GetX()), tomm(bb.GetY()), tomm(bb.GetRight()), tomm(bb.GetBottom()))

    @staticmethod
    def _close(box, x, y, d=1.2):
        return box[0] - d <= x <= box[2] + d and box[1] - d <= y <= box[3] + d

    def ok(self, x, y):
        if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in self.excl):
            return False
        p = V(x, y)
        if any(z.Outline().Contains(p) for z in self.rules):
            return False
        ring = [V(x + self.r * math.cos(a), y + self.r * math.sin(a)) for a in
                [k * math.pi / 4 for k in range(8)]] + [p]
        # Must sit inside GND pour on every layer in pour_layers (4-layer: B.Cu and the In2 plane; 2-layer:
        # both outer layers); elsewhere it only needs clearance from other nets' tracks.
        for layer in self.pour_layers:
            if not all(any(z.HitTestFilledArea(layer, q) for z in self.zones) for q in ring):
                return False
        for t, bx in self.tracks:
            if self._close(bx, x, y) and t.HitTest(p, mm(0.3 + 0.17)):
                return False
        if not self.b.GetBoardEdgesBoundingBox().Contains(p):
            return False
        # copper-to-edge 0.3 mm (outline, chamfers and slots) plus the via radius
        if not hasattr(self, '_edges'):
            self._edges = [d for d in self.b.GetDrawings() if d.GetLayer() == pcb.Edge_Cuts]
        if any(e.HitTest(p, mm(0.3 + 0.3 + 0.05)) for e in self._edges):
            return False
        for pad, bx in self.pads:
            gap = self.gnd_pad_gap if pad.GetNetCode() == self.gnd else self.pad_gap
            if self._close(bx, x, y) and pad.HitTest(p, mm(0.3 + gap)):
                return False
        for pos, rad in self.holes:
            if math.hypot(tomm(pos.x) - x, tomm(pos.y) - y) < rad + 0.3 + 0.35:
                return False
        if any(math.hypot(vx - x, vy - y) < 0.6 + self.via_gap for vx, vy in self.vias):
            return False
        return True

    def add(self, x, y):
        if self.ok(x, y):
            via(self.b, 'GND', x, y)
            self.vias.append((x, y)); self.added.append((x, y))
            return True
        return False

    def near(self, x, y, rmin=0.7, rmax=2.6, have=1.2, step=0.1):
        """Add one via as close as possible to (x, y) unless a via is already within `have` mm."""
        if any(math.hypot(vx - x, vy - y) < have for vx, vy in self.vias):
            return None
        n = int(rmax / step)
        cand = sorted(((i * step, j * step) for i in range(-n, n + 1) for j in range(-n, n + 1)),
                      key=lambda d: math.hypot(*d))
        for dx, dy in cand:
            r = math.hypot(dx, dy)
            if r < rmin:
                continue
            if r > rmax:
                break
            if self.add(round(x + dx, 3), round(y + dy, 3)):
                return self.added[-1]
        return None

    def grid(self, x0, y0, x1, y1, pitch):
        n = 0
        y = y0
        while y <= y1:
            x = x0
            while x <= x1:
                n += self.add(round(x, 3), round(y, 3))
                x += pitch
            y += pitch
        return n

    def perimeter(self, w, h, inset, pitch):
        n = 0
        for x in frange(inset, w - inset, pitch):
            n += self.add(x, inset) + self.add(x, h - inset)
        for y in frange(inset, h - inset, pitch):
            n += self.add(inset, y) + self.add(w - inset, y)
        return n


def frange(a, z, step):
    out, v = [], a
    while v <= z + 1e-9:
        out.append(round(v, 3)); v += step
    return out
