"""Small pcbnew helpers for scripted Rev B layout edits (run with KiCad Python)."""
import math
import pcbnew as pcb

mm = pcb.FromMM
LAYER = {'F': pcb.F_Cu, 'In1': pcb.In1_Cu, 'In2': pcb.In2_Cu, 'B': pcb.B_Cu}


def V(x, y):
    return pcb.VECTOR2I(mm(x), mm(y))


def netinfo(b, name):
    n = b.FindNet(name)
    if n is None:
        raise KeyError(name)
    return n


def track(b, net, layer, pts, w=0.2):
    """Add a polyline of segments; pts are (x, y) in mm."""
    for a, z in zip(pts, pts[1:]):
        t = pcb.PCB_TRACK(b)
        t.SetStart(V(*a)); t.SetEnd(V(*z)); t.SetWidth(mm(w)); t.SetLayer(LAYER[layer])
        t.SetNet(netinfo(b, net)); b.Add(t)


def via(b, net, x, y, d=0.6, drill=0.3):
    v = pcb.PCB_VIA(b)
    v.SetPosition(V(x, y)); v.SetWidth(mm(d)); v.SetDrill(mm(drill))
    v.SetLayerPair(pcb.F_Cu, pcb.B_Cu); v.SetNet(netinfo(b, net)); b.Add(v)
    return v


def ripup(b, nets, box=None, layers=None):
    """Remove tracks/vias of the given nets, optionally only those touching box (x0,y0,x1,y1)
    and only on the given layers ('F', 'In1', 'In2', 'B', or 'via')."""
    def inside(p):
        return box is None or (box[0] <= pcb.ToMM(p.x) <= box[2] and box[1] <= pcb.ToMM(p.y) <= box[3])

    def on(t):
        if layers is None:
            return True
        if t.Type() == pcb.PCB_VIA_T:
            return 'via' in layers
        return any(LAYER.get(l) == t.GetLayer() for l in layers)
    doomed = [t for t in b.GetTracks() if t.GetNetname() in nets and on(t)
              and (inside(t.GetStart()) or inside(t.GetEnd()))]
    for t in doomed:
        b.Delete(t)
    return len(doomed)


def move(b, ref, x, y, rot=None):
    f = next(f for f in b.GetFootprints() if f.GetReference() == ref)
    f.SetPosition(V(x, y))
    if rot is not None:
        f.SetOrientationDegrees(rot)
    return f


def orient(b, ref, x, y, first_pad_up=True):
    """Place a 2-pad part vertically at (x, y) with pad 1 above (smaller y) or below pad 2."""
    f = move(b, ref, x, y, 90)
    p1, p2 = sorted(f.Pads(), key=lambda p: p.GetNumber())[:2]
    if (p1.GetPosition().y < p2.GetPosition().y) != first_pad_up:
        f.SetOrientationDegrees(270)
    return f


def pads_of(b, ref):
    f = next(f for f in b.GetFootprints() if f.GetReference() == ref)
    return {p.GetNumber(): (pcb.ToMM(p.GetPosition().x), pcb.ToMM(p.GetPosition().y)) for p in f.Pads()}


def orient_to(b, ref, x, y, want):
    """Place ref at (x, y), trying all rotations until every pad in `want` {pad: (dx_sign, dy_sign)}
    lies on the requested side of the centre (sign 0 = aligned with the centre)."""
    f = next(f for f in b.GetFootprints() if f.GetReference() == ref)
    f.SetPosition(V(x, y))
    for rot in (0, 90, 180, 270):
        f.SetOrientationDegrees(rot)
        pp = pads_of(b, ref)
        sgn = lambda v: 0 if abs(v) < 0.05 else (1 if v > 0 else -1)
        if all((sgn(pp[n][0] - x), sgn(pp[n][1] - y)) == s for n, s in want.items()):
            return rot
    raise ValueError(f'no rotation of {ref} matches {want}')


def free_via(b, net, x, y, rmax=1.6, step=0.1, gap=0.17, optional=False):
    """Place a via of `net` at the free spot nearest (x, y): clear of every other net's pads, tracks and
    vias on all layers, of holes, rule areas and the board edge. Returns (x, y)."""
    code = netinfo(b, net).GetNetCode()
    items = [t for t in b.GetTracks() if t.GetNetCode() != code]
    pads = [p for f in b.GetFootprints() for p in f.Pads()]
    rules = [z for z in b.Zones() if z.GetIsRuleArea()]
    edge = b.GetBoardEdgesBoundingBox()
    n = int(rmax / step)
    for dx, dy in sorted(((i * step, j * step) for i in range(-n, n + 1) for j in range(-n, n + 1)),
                         key=lambda d: math.hypot(*d)):
        if math.hypot(dx, dy) > rmax:
            break
        px, py = round(x + dx, 3), round(y + dy, 3); p = V(px, py)
        if not (edge.GetX() + mm(0.8) < p.x < edge.GetRight() - mm(0.8) and
                edge.GetY() + mm(0.8) < p.y < edge.GetBottom() - mm(0.8)):
            continue
        if any(z.Outline().Contains(p) for z in rules):
            continue
        if any(t.HitTest(p, mm(0.3 + gap + (0.3 if t.Type() == pcb.PCB_VIA_T else 0))) for t in items):
            continue
        bad = False
        for pad in pads:
            same = pad.GetNetCode() == code
            if pad.GetDrillSize().x > 0 and pad.HitTest(p, mm(0.3 + 0.3)):
                bad = True; break
            if not same and pad.HitTest(p, mm(0.3 + gap)):
                bad = True; break
        if bad:
            continue
        via(b, net, px, py)
        return px, py
    if optional:
        print(f'  note: no free via spot for {net} near ({x}, {y})')
        return None
    raise ValueError(f'no free via spot for {net} near ({x}, {y})')


def place_header(b, ref, x1, y):
    """Right-angle 1xN header: pin 1 at (x1, y), pins toward +x, plastic body toward +y (board edge)."""
    f = next(f for f in b.GetFootprints() if f.GetReference() == ref)
    for rot in (0, 90, 180, 270):
        f.SetOrientationDegrees(rot); f.SetPosition(V(x1, y))
        pp = pads_of(b, ref)
        bb = f.GetBoundingBox(False)
        if abs(pp['2'][1] - y) < 0.05 and pp['2'][0] > x1 and pcb.ToMM(bb.Centre().y) > y + 1:
            return pp
    raise ValueError(f'cannot orient {ref}')


def _touch(item, p, layer):
    """True if point p on layer lands on item copper (track body, via, pad)."""
    if isinstance(item, pcb.PAD):
        return item.IsOnLayer(layer) and item.HitTest(p, 0)
    if item.Type() == pcb.PCB_VIA_T:
        return item.HitTest(p, 0)
    return item.GetLayer() == layer and item.HitTest(p, 0)


def prune(b, keep_nets=('GND',)):
    """Iteratively delete track ends that touch nothing and vias with fewer than two connections.
    GND vias and locked items are kept; unlocked GND tracks are pruned like any other."""
    pads = [p for f in b.GetFootprints() for p in f.Pads()]
    zones = [z for z in b.Zones() if not z.GetIsRuleArea()]

    def in_zone(t, p):
        return any(z.GetNetCode() == t.GetNetCode() and z.HitTestFilledArea(t.GetLayer(), p) for z in zones)
    removed = 0
    while True:
        items = list(b.GetTracks())
        by_net = {}
        for it in items + pads:
            by_net.setdefault(it.GetNetCode(), []).append(it)
        doomed = []
        for t in items:
            if t.IsLocked():                         # deliberate pre-routes (may end in a pour) stay
                continue
            peers = [o for o in by_net[t.GetNetCode()] if o is not t]
            if t.Type() == pcb.PCB_VIA_T:
                if t.GetNetname() in keep_nets:
                    continue
                p = t.GetPosition()
                hits = [o for o in peers if (isinstance(o, pcb.PAD) and o.HitTest(p, 0)) or
                        (not isinstance(o, pcb.PAD) and o.Type() != pcb.PCB_VIA_T and
                         (o.GetStart() == p or o.GetEnd() == p or o.HitTest(p, 0)))]
                if len({(h.GetLayer() if not isinstance(h, pcb.PAD) else -1) for h in hits}) < 2 and not \
                        any(isinstance(h, pcb.PAD) and h.GetAttribute() == pcb.PAD_ATTRIB_PTH for h in hits):
                    doomed.append(t)
                continue
            if t.GetLength() == 0:
                doomed.append(t); continue
            for p in (t.GetStart(), t.GetEnd()):
                if not any(_touch(o, p, t.GetLayer()) for o in peers) and not in_zone(t, p):
                    doomed.append(t); break
        if not doomed:
            return removed
        for t in doomed:
            b.Delete(t)
        removed += len(doomed)


def refill(b):
    pcb.ZONE_FILLER(b).Fill(b.Zones())


def dist(a, z):
    return math.hypot(a[0] - z[0], a[1] - z[1])
