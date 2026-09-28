"""Finish the connections an autorouter left open (run with KiCad's Python).

Reads a kicad-cli DRC report (JSON) and, for every unconnected pair that is not GND, routes one path on
F.Cu/B.Cu with vias using A* on a 0.1 mm grid. Obstacles come from KiCad's own hit tests (pads, tracks,
vias of other nets, the board edge and track keepouts), inflated by clearance + half the track width, so a
found path is DRC-clean by construction. GND is left to the pours and stitching.

Usage: astar_finish.py <board.kicad_pcb> <drc.json>
       astar_finish.py gnd <board.kicad_pcb>   (join isolated GND pour pockets to the main plane)
"""
import heapq, json, math, re, sys
import pcbnew as pcb

GRID = 0.1
CLEAR = 0.15 + 0.02          # net clearance plus a little margin for grid rounding
EDGE = 0.3 + 0.05
VIA_D, VIA_DRILL = 0.6, 0.3
VIA_COST = 12.0              # in grid steps
FRONT_COST = 1.4             # prefer the back (component side) so the front stays ground
MARGIN = 6.0                 # search window around the two ends, mm
W = {'Power': 0.3, 'PowerLow': 0.3}


def mm(v):
    return pcb.ToMM(v)


def nm(v):
    return pcb.FromMM(v)


class Grid:
    def __init__(self, b, net, x0, y0, x1, y1, width, soft=False, soft_power=False):
        self.b, self.net, self.w, self.soft, self.soft_power = b, net, width, soft, soft_power
        self.x0, self.y0 = x0, y0
        self.nx, self.ny = int((x1 - x0) / GRID) + 1, int((y1 - y0) / GRID) + 1
        self.block = {pcb.F_Cu: bytearray(self.nx * self.ny), pcb.B_Cu: bytearray(self.nx * self.ny)}
        self.novia = bytearray(self.nx * self.ny)
        self._mark()

    def xy(self, i, j):
        return self.x0 + i * GRID, self.y0 + j * GRID

    def ij(self, x, y):
        return int(round((x - self.x0) / GRID)), int(round((y - self.y0) / GRID))

    def _cells(self, bb, grow):
        i0, j0 = self.ij(mm(bb.GetX()) - grow, mm(bb.GetY()) - grow)
        i1, j1 = self.ij(mm(bb.GetRight()) + grow, mm(bb.GetBottom()) + grow)
        for j in range(max(j0, 0), min(j1, self.ny - 1) + 1):
            for i in range(max(i0, 0), min(i1, self.nx - 1) + 1):
                yield i, j

    def _mark(self):
        b, t_inf, v_inf = self.b, CLEAR + self.w / 2, CLEAR + VIA_D / 2
        items = []
        for f in b.GetFootprints():
            for p in f.Pads():
                items.append(p)
        items += list(b.GetTracks())
        for it in items:
            hole = 0.0
            if isinstance(it, pcb.PAD) and it.GetDrillSize().x > 0:
                hole = mm(max(it.GetDrillSize().x, it.GetDrillSize().y)) / 2
            elif it.Type() == pcb.PCB_VIA_T:
                hole = mm(it.GetDrillValue()) / 2
            if hole:
                q = it.GetPosition(); lim = hole + VIA_DRILL / 2 + 0.25 + 0.05
                for i, j in self._cells(it.GetBoundingBox(), lim):
                    x, y = self.xy(i, j)
                    if math.hypot(x - mm(q.x), y - mm(q.y)) < lim:
                        self.novia[j * self.nx + i] = 1
            if it.GetNetname() == self.net and self.net:
                continue
            if self.soft and not isinstance(it, pcb.PAD) and not it.IsLocked() and it.GetNetname() != 'GND' and \
                    (self.soft_power or not it.GetNetname().startswith('+')):
                continue                        # rip-up search: movable signal copper is not an obstacle
            is_pad = isinstance(it, pcb.PAD)
            layers = [l for l in (pcb.F_Cu, pcb.B_Cu) if it.IsOnLayer(l)]
            if is_pad and it.GetDrillSize().x > 0:
                layers = [pcb.F_Cu, pcb.B_Cu]
            if not layers:
                continue
            bb = it.GetBoundingBox()
            for i, j in self._cells(bb, v_inf):
                x, y = self.xy(i, j)
                p = pcb.VECTOR2I(nm(x), nm(y))
                k = j * self.nx + i
                if it.HitTest(p, nm(v_inf)):
                    self.novia[k] = 1
                    if it.HitTest(p, nm(t_inf)):
                        for l in layers:
                            self.block[l][k] = 1
        # Holes of any net keep vias away (hole-to-hole).
        # Board edge and rule areas that forbid tracks/vias.
        edges = [d for d in b.GetDrawings() if d.GetLayer() == pcb.Edge_Cuts]
        rules = [z for z in b.Zones() if z.GetIsRuleArea() and (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias())]
        outline = b.GetBoardEdgesBoundingBox()
        for j in range(self.ny):
            for i in range(self.nx):
                x, y = self.xy(i, j)
                p = pcb.VECTOR2I(nm(x), nm(y))
                k = j * self.nx + i
                if not outline.Contains(p) or any(e.HitTest(p, nm(EDGE + VIA_D / 2)) for e in edges
                                                  if self._near(e, x, y)):
                    self.novia[k] = 1
                    if not outline.Contains(p) or any(e.HitTest(p, nm(EDGE + self.w / 2)) for e in edges
                                                      if self._near(e, x, y)):
                        self.block[pcb.F_Cu][k] = self.block[pcb.B_Cu][k] = 1
                for z in rules:
                    if z.Outline().Contains(p):
                        for l in (pcb.F_Cu, pcb.B_Cu):
                            if z.IsOnLayer(l) and z.GetDoNotAllowTracks():
                                self.block[l][k] = 1
                        if z.GetDoNotAllowVias():
                            self.novia[k] = 1
        # Inside the board outline but outside the real (chamfered/slotted) shape: use a polygon test.
        poly = pcb.SHAPE_POLY_SET()
        b.GetBoardPolygonOutlines(poly, True)
        for j in range(self.ny):
            for i in range(self.nx):
                x, y = self.xy(i, j)
                if not poly.Contains(pcb.VECTOR2I(nm(x), nm(y))):
                    k = j * self.nx + i
                    self.novia[k] = 1
                    self.block[pcb.F_Cu][k] = self.block[pcb.B_Cu][k] = 1

    @staticmethod
    def _near(e, x, y, d=1.5):
        bb = e.GetBoundingBox()
        return mm(bb.GetX()) - d <= x <= mm(bb.GetRight()) + d and mm(bb.GetY()) - d <= y <= mm(bb.GetBottom()) + d


def astar(g, starts, goals):
    """starts/goals: sets of (layer, i, j). Returns list of (layer, i, j)."""
    L = (pcb.F_Cu, pcb.B_Cu)
    gx = [(i, j) for _, i, j in goals]
    gi = sum(i for i, _ in gx) / len(gx); gj = sum(j for _, j in gx) / len(gx)

    spread = max(max(i for i, _ in gx) - min(i for i, _ in gx), max(j for _, j in gx) - min(j for _, j in gx))

    def h(i, j):                                  # goals spread over the board: plain Dijkstra
        return 0.0 if spread > 40 else math.hypot(i - gi, j - gj) * 0.9
    openq, best, prev = [], {}, {}
    for s in starts:
        best[s] = 0.0
        heapq.heappush(openq, (h(s[1], s[2]), 0.0, s))
    steps = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    n = 0
    while openq:
        f, c, s = heapq.heappop(openq)
        if c > best.get(s, 1e18):
            continue
        if s in goals:
            path = [s]
            while s in prev:
                s = prev[s]; path.append(s)
            return path[::-1]
        n += 1
        if n > 6_000_000:
            return None
        l, i, j = s
        lc = FRONT_COST if l == pcb.F_Cu else 1.0
        for di, dj, sc in steps:
            a, bj = i + di, j + dj
            if 0 <= a < g.nx and 0 <= bj < g.ny and (not g.block[l][bj * g.nx + a] or (l, a, bj) in goals):
                t = (l, a, bj); nc = c + sc * lc
                if nc < best.get(t, 1e18):
                    best[t] = nc; prev[t] = s; heapq.heappush(openq, (nc + h(a, bj), nc, t))
        k = j * g.nx + i
        if not g.novia[k]:
            o = L[1] if l == L[0] else L[0]
            if not g.block[o][k] or (o, i, j) in goals:
                t = (o, i, j); nc = c + VIA_COST
                if nc < best.get(t, 1e18):
                    best[t] = nc; prev[t] = s; heapq.heappush(openq, (nc + h(i, j), nc, t))
    return None


def item_at(b, net, x, y):
    p = pcb.VECTOR2I(nm(x), nm(y))
    for f in b.GetFootprints():
        for pad in f.Pads():
            if pad.GetNetname() == net and pad.HitTest(p, nm(0.01)):
                return pad
    for t in b.GetTracks():
        if t.GetNetname() == net and t.HitTest(p, nm(0.01)):
            return t
    return None


def cells_of(g, it):
    out = set()
    layers = [l for l in (pcb.F_Cu, pcb.B_Cu) if it.IsOnLayer(l)]
    if isinstance(it, pcb.PAD) and it.GetDrillSize().x > 0:
        layers = [pcb.F_Cu, pcb.B_Cu]
    for i, j in g._cells(it.GetBoundingBox(), 0):
        x, y = g.xy(i, j)
        if it.HitTest(pcb.VECTOR2I(nm(x), nm(y)), 0):
            for l in layers:
                out.add((l, i, j))
    return out


def emit(b, g, net, path, width, made=None):
    ni = b.FindNet(net)
    pts = [(path[0][0], g.xy(path[0][1], path[0][2]))]
    for (l0, i0, j0), (l1, i1, j1) in zip(path, path[1:]):
        if l1 != l0:
            v = pcb.PCB_VIA(b); v.SetPosition(pcb.VECTOR2I(nm(g.xy(i0, j0)[0]), nm(g.xy(i0, j0)[1])))
            v.SetWidth(nm(VIA_D)); v.SetDrill(nm(VIA_DRILL)); v.SetLayerPair(pcb.F_Cu, pcb.B_Cu); v.SetNet(ni); b.Add(v)
            if made is not None:
                made.append(v)
        pts.append((l1, g.xy(i1, j1)))
    # merge collinear runs per layer
    segs, run = [], [pts[0]]
    for q in pts[1:]:
        if q[0] != run[-1][0]:
            segs.append(run); run = [q]
        else:
            run.append(q)
    segs.append(run)
    n = 0
    for run in segs:
        simp = [run[0]]
        for k in range(1, len(run) - 1):
            (_, a), (_, c), (_, d) = simp[-1], run[k], run[k + 1]
            if abs((c[0] - a[0]) * (d[1] - a[1]) - (c[1] - a[1]) * (d[0] - a[0])) > 1e-6:
                simp.append(run[k])
        simp.append(run[-1])
        for (l, a), (_, z) in zip(simp, simp[1:]):
            if a == z:
                continue
            t = pcb.PCB_TRACK(b)
            t.SetStart(pcb.VECTOR2I(nm(a[0]), nm(a[1]))); t.SetEnd(pcb.VECTOR2I(nm(z[0]), nm(z[1])))
            t.SetWidth(nm(width)); t.SetLayer(l); t.SetNet(ni); b.Add(t); n += 1
            if made is not None:
                made.append(t)
    return n


def ripup_route(b, net, width, win):
    """Route `net` ignoring movable copper of other nets, then delete the movable tracks/vias it collides with.
    Returns the set of nets that lost copper (to be rerouted), or None if even that search fails."""
    cl = clusters(b, net)
    if len(cl) < 2:
        return set()
    cl.sort(key=len)
    src, rest = cl[0], [it for c in cl[1:] for it in c]
    g = Grid(b, net, *win, width, soft=True)
    path = astar(g, set().union(*[cells_of(g, it) for it in src]), set().union(*[cells_of(g, it) for it in rest]))
    if not path:
        return None
    made = []
    emit(b, g, net, path, width, made)
    return rip_conflicts(b, made, width, net)


def rip_conflicts(b, made, width, net, power=False):
    """Delete movable signal tracks/vias that collide with the new copper in `made`; return their nets."""
    victims = []
    for t in list(b.GetTracks()):
        if t.GetNetname() == net or t.IsLocked() or t.GetNetname() == 'GND' or \
                (t.GetNetname().startswith('+') and not power):
            continue
        for m in made:
            if m.Type() == pcb.PCB_VIA_T:
                hit = t.HitTest(m.GetPosition(), nm(CLEAR + VIA_D / 2)) if (t.Type() == pcb.PCB_VIA_T or
                                                                             t.IsOnLayer(pcb.F_Cu) or t.IsOnLayer(pcb.B_Cu)) else False
            else:
                if t.Type() != pcb.PCB_VIA_T and t.GetLayer() != m.GetLayer():
                    continue
                a, z = m.GetStart(), m.GetEnd()
                L = max(1, int(math.hypot(z.x - a.x, z.y - a.y) / nm(0.05)))
                hit = any(t.HitTest(pcb.VECTOR2I(a.x + (z.x - a.x) * k // L, a.y + (z.y - a.y) * k // L),
                                    nm(CLEAR + width / 2)) for k in range(L + 1))
            if hit:
                victims.append(t); break
    nets = {t.GetNetname() for t in victims}
    for t in victims:
        b.Delete(t)
    return nets


def clusters(b, net, skip=None):
    """Group the net's pads, tracks and vias into connected clusters (ignoring pours); `skip` is left out."""
    items = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == net]
    items += [t for t in b.GetTracks() if t.GetNetname() == net and not (skip is not None and t.m_Uuid == skip.m_Uuid)]
    parent = list(range(len(items)))

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]; k = parent[k]
        return k

    def layers(it):
        if isinstance(it, pcb.PAD) and it.GetDrillSize().x > 0 or it.Type() == pcb.PCB_VIA_T:
            return {pcb.F_Cu, pcb.B_Cu}
        return {l for l in (pcb.F_Cu, pcb.B_Cu) if it.IsOnLayer(l)}

    def points(it):
        if it.Type() == pcb.PCB_TRACE_T:
            return [it.GetStart(), it.GetEnd()]
        return [it.GetPosition()]
    for a in range(len(items)):
        for c in range(a + 1, len(items)):
            A, C = items[a], items[c]
            if not (layers(A) & layers(C)):
                continue
            if any(C.HitTest(q, 0) for q in points(A)) or any(A.HitTest(q, 0) for q in points(C)):
                parent[find(a)] = find(c)
    groups = {}
    for k, it in enumerate(items):
        groups.setdefault(find(k), []).append(it)
    return list(groups.values())


def netclass_width(b, net):
    """Power nets ('+...', Power class 0.6 mm) get 0.5 mm here so they still fit; +3V3_CO2 (PowerLow) 0.3 mm."""
    if net == '+3V3_CO2':
        return 0.3
    return 0.5 if net.startswith('+') else 0.2


def main(board, report):
    b = pcb.LoadBoard(board)
    d = json.loads(open(report).read())
    nets = []
    for u in d.get('unconnected_items', []):
        for it in u['items']:
            m = re.search(r'\[([^\]]+)\]', it['description'])
            if m and m.group(1) != 'GND' and m.group(1) not in nets:
                nets.append(m.group(1))
    bb = b.GetBoardEdgesBoundingBox()
    full = (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))
    ripups = {}
    k = 0
    while k < len(nets):
        net = nets[k]; k += 1
        width = netclass_width(b, net)
        for _ in range(8):
            cl = clusters(b, net)
            if len(cl) < 2:
                break
            cl.sort(key=len)
            src, rest = cl[0], [it for c in cl[1:] for it in c]
            pos = [(mm(it.GetPosition().x), mm(it.GetPosition().y)) for it in src + rest]
            routed = False
            for margin in (MARGIN, 14.0, None):
                if margin is None:
                    win = full
                else:
                    xs = [p[0] for p in pos]; ys = [p[1] for p in pos]
                    sx = [mm(it.GetPosition().x) for it in src]; sy = [mm(it.GetPosition().y) for it in src]
                    # window around the source cluster and its nearest other item
                    near = min(rest, key=lambda it: math.hypot(mm(it.GetPosition().x) - sx[0], mm(it.GetPosition().y) - sy[0]))
                    xs = sx + [mm(near.GetPosition().x)]; ys = sy + [mm(near.GetPosition().y)]
                    win = (max(min(xs) - margin, full[0]), max(min(ys) - margin, full[1]),
                           min(max(xs) + margin, full[2]), min(max(ys) + margin, full[3]))
                g = Grid(b, net, *win, width)
                starts = set().union(*[cells_of(g, it) for it in src])
                goals = set().union(*[cells_of(g, it) for it in rest])
                if not starts or not goals:
                    continue
                path = astar(g, starts, goals)
                if path:
                    n = emit(b, g, net, path, width)
                    print(f'routed {net}: {n} segments, width {width}, window {tuple(round(v, 1) for v in win)}')
                    routed = True
                    break
            if not routed and width > 0.3:
                print('narrowing', net, 'to 0.3 mm'); width = 0.3
                continue
            if not routed and ripups.get(net, 0) < 3:
                ripups[net] = ripups.get(net, 0) + 1
                lost = ripup_route(b, net, width, full)
                if lost is not None:
                    print(f'rip-up for {net}: removed copper of {sorted(lost)}')
                    for other in sorted(lost):
                        if other not in nets:
                            nets.append(other)
                    continue
            if not routed:
                print('FAILED', net, 'width', width)
                break
    pcb.SaveBoard(board, b)


def gnd_islands(board, rounds=3):
    """Join GND pour pockets that hold pads but no path to the main plane: A* from the pocket's pads to any
    cell of a main-plane island (either layer), with a 0.3 mm track and vias as needed."""
    from main_revb_2layer_finish import islands
    b = pcb.LoadBoard(board)
    for _ in range(rounds):
        pcb.ZONE_FILLER(b).Fill(b.Zones())
        isl, find = islands(b)
        main = find(max(range(len(isl)), key=lambda n: isl[n][3]))
        gpads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == 'GND']
        comps = {}
        for n, (l, polys, k, a) in enumerate(isl):
            if find(n) != main:
                comps.setdefault(find(n), []).append(n)
        joined = 0
        for c, ns in comps.items():
            src = [p for p in gpads for n in ns if p.IsOnLayer(isl[n][0]) and isl[n][1].Contains(p.GetPosition(), isl[n][2])]
            if not src:
                continue
            xs = [mm(p.GetPosition().x) for p in src]; ys = [mm(p.GetPosition().y) for p in src]
            bb = b.GetBoardEdgesBoundingBox()
            win = (max(min(xs) - 8, mm(bb.GetX())), max(min(ys) - 8, mm(bb.GetY())),
                   min(max(xs) + 8, mm(bb.GetRight())), min(max(ys) + 8, mm(bb.GetBottom())))
            g = Grid(b, 'GND', *win, 0.3)
            starts = set().union(*[cells_of(g, p) for p in src])
            mains = [m for m in range(len(isl)) if find(m) == main]
            goals = set()
            for j in range(g.ny):
                for i in range(g.nx):
                    x, y = g.xy(i, j); q = pcb.VECTOR2I(nm(x), nm(y))
                    for m in mains:
                        l, polys, k, _ = isl[m]
                        if not g.block[l][j * g.nx + i] and polys.Contains(q, k):
                            goals.add((l, i, j))
            if not starts or not goals:
                continue
            path = astar(g, starts, goals)
            if path:
                emit(b, g, 'GND', path, 0.3); joined += 1
            else:                                   # rip up signal tracks in the way (not power, not locked)
                gs = Grid(b, 'GND', *win, 0.3, soft=True, soft_power=True)
                goals = {c for c in goals} | {(l, i, j) for (l, i, j) in goals}
                path = astar(gs, set().union(*[cells_of(gs, p) for p in src]), goals)
                if path:
                    made = []
                    emit(b, gs, 'GND', path, 0.3, made)
                    lost = rip_conflicts(b, made, 0.3, 'GND', power=True)
                    print('gnd rip-up removed copper of', sorted(lost)); joined += 1
        print(f'gnd: {len(comps)} separate pockets, {joined} joined')
        if not joined:
            break
    pcb.ZONE_FILLER(b).Fill(b.Zones())
    pcb.SaveBoard(board, b)


def route_hard(b, net, full):
    """Connect all clusters of `net` without disturbing any other copper. True when fully connected."""
    for width in ((netclass_width(b, net), 0.3) if netclass_width(b, net) > 0.3 else (netclass_width(b, net),)):
        for _ in range(8):
            cl = clusters(b, net)
            if len(cl) < 2:
                return True
            cl.sort(key=len)
            g = Grid(b, net, *full, width)
            path = astar(g, set().union(*[cells_of(g, it) for it in cl[0]]),
                         set().union(*[cells_of(g, it) for c in cl[1:] for it in c]))
            if not path:
                break
            emit(b, g, net, path, width)
    return len(clusters(b, net)) < 2


def gnd_fix_verified(board):
    """Join each isolated GND pocket (with pads) to the main plane. A variant is kept only if every net it
    displaces can be rerouted without displacing anything else; otherwise the board is restored."""
    import shutil, tempfile
    from main_revb_2layer_finish import islands
    tmp = tempfile.mktemp(suffix='.kicad_pcb')
    b = pcb.LoadBoard(board)
    bb = b.GetBoardEdgesBoundingBox()
    full = (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))
    for attempt in range(6):
        pcb.ZONE_FILLER(b).Fill(b.Zones())
        isl, find = islands(b)
        main = find(max(range(len(isl)), key=lambda n: isl[n][3]))
        gpads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == 'GND']
        comps = {}
        for n, (l, polys, k, a) in enumerate(isl):
            if find(n) != main:
                comps.setdefault(find(n), []).append(n)
        pockets = []
        for c, ns in comps.items():
            src = [p for p in gpads for n in ns if p.IsOnLayer(isl[n][0]) and isl[n][1].Contains(p.GetPosition(), isl[n][2])]
            if src:
                pockets.append(src)
        print(f'attempt {attempt}: {len(pockets)} pockets with pads')
        if not pockets:
            break
        progress = False
        for src in pockets:
            pcb.SaveBoard(tmp, b)
            xs = [mm(p.GetPosition().x) for p in src]; ys = [mm(p.GetPosition().y) for p in src]
            for margin, power in ((4, False), (4, True), (8, False), (8, True)):
                win = (max(min(xs) - margin, full[0]), max(min(ys) - margin, full[1]),
                       min(max(xs) + margin, full[2]), min(max(ys) + margin, full[3]))
                g = Grid(b, 'GND', *win, 0.3, soft=True, soft_power=power)
                mains = [m for m in range(len(isl)) if find(m) == main]
                goals = set()
                for j in range(g.ny):
                    for i in range(g.nx):
                        x, y = g.xy(i, j); q = pcb.VECTOR2I(nm(x), nm(y))
                        for m in mains:
                            l, polys, k, _ = isl[m]
                            if not g.block[l][j * g.nx + i] and polys.Contains(q, k):
                                goals.add((l, i, j))
                path = astar(g, set().union(*[cells_of(g, p) for p in src]), goals) if goals else None
                if not path:
                    continue
                made = []
                emit(b, g, 'GND', path, 0.3, made)
                lost = rip_conflicts(b, made, 0.3, 'GND', power=power)
                ok = all(route_hard(b, n, full) for n in sorted(lost))
                if ok:
                    print(f'  joined pocket at {src[0].GetParentFootprint().GetReference()}; rerouted {sorted(lost)}')
                    progress = True
                    break
                b = pcb.LoadBoard(tmp)                           # roll back this variant
                pcb.ZONE_FILLER(b).Fill(b.Zones())
                isl, find = islands(b)
                main = find(max(range(len(isl)), key=lambda n: isl[n][3]))
                src = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == 'GND' and
                       any(abs(p.GetPosition().x - q.GetPosition().x) < 10 and abs(p.GetPosition().y - q.GetPosition().y) < 10
                           for q in src)] if False else [p for f in b.GetFootprints() for p in f.Pads()
                                                          if (f.GetReference(), p.GetNumber()) in
                                                          {(q.GetParentFootprint().GetReference(), q.GetNumber()) for q in src}]
            else:
                print(f'  could not join pocket at {src[0].GetParentFootprint().GetReference()}')
        if not progress:
            break
    pcb.ZONE_FILLER(b).Fill(b.Zones())
    pcb.SaveBoard(board, b)


def route_verified(board, nets, depth=2):
    """Connect each net, displacing movable copper (signals and power, never GND or locked) only when every
    displaced net can then be reconnected (recursively, up to `depth`). Rolls back failed attempts."""
    import tempfile
    tmp = tempfile.mktemp(suffix='.kicad_pcb')
    b = pcb.LoadBoard(board)
    bb = b.GetBoardEdgesBoundingBox()
    full = (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))

    def attempt(b, net, d):
        if route_hard(b, net, full):
            return True
        if d == 0:
            return False
        for width in (0.3, 0.2) if net.startswith('+') else (0.2,):
            cl = clusters(b, net)
            if len(cl) < 2:
                return True
            cl.sort(key=len)
            g = Grid(b, net, *full, width, soft=True, soft_power=True)
            path = astar(g, set().union(*[cells_of(g, it) for it in cl[0]]),
                         set().union(*[cells_of(g, it) for c in cl[1:] for it in c]))
            if not path:
                continue
            made = []
            emit(b, g, net, path, width, made)
            lost = rip_conflicts(b, made, width, net, power=True)
            if all(attempt(b, n, d - 1) for n in sorted(lost)) and len(clusters(b, net)) < 2:
                print(f'  {net}: displaced {sorted(lost)}, all reconnected')
                return True
            return False
        return False
    for net in nets:
        pcb.SaveBoard(tmp, b)
        if attempt(b, net, depth):
            print('routed', net)
        else:
            print('FAILED', net, '(rolled back)')
            b = pcb.LoadBoard(tmp)
    pcb.SaveBoard(board, b)


if __name__ == '__main__':
    if sys.argv[1] == 'gnd':
        gnd_islands(sys.argv[2])
        sys.exit()
    if sys.argv[1] == 'verified':
        import os
        route_verified(sys.argv[2], sys.argv[3:], depth=int(os.environ.get('DEPTH', 2)))
        sys.exit()
    if sys.argv[1] == 'gndfix':
        gnd_fix_verified(sys.argv[2])
        sys.exit()
    main(sys.argv[1], sys.argv[2])
