"""Rev B main board, 2-layer finish (run with KiCad's Python) after main_revb_2layer.py import.

  stitch  - refill the F.Cu/B.Cu GND pours and add stitching vias: one beside each ground pad of the fitted
            parts, a 2 mm edge fence and a 3 mm field grid (the CO2 island keeps its own isolation).
  repair  - find GND pour islands not joined to the main plane and add a via in each where the other
            layer is main plane; repeat until nothing changes.
"""
from pathlib import Path
import json, sys
import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pcb_edit import refill, prune
from ground import Stitcher

ROOT = Path(__file__).resolve().parents[1] / 'main'
BOARD = ROOT / 'AQI_Main.kicad_pcb'
X0, X1, H = -1.5, 45.5, 76.0                   # board edges after the 1.5 mm side widening
CO2_ISLAND = (27.0, 20.5, 45.5, 35.5)          # island at the top of the right column
BOTH = (pcb.F_Cu, pcb.B_Cu)


def stitch(b):
    # Fill without island removal first so every region that could carry a stitching via is visible.
    pours = [z for z in b.Zones() if not z.GetIsRuleArea()]
    modes = [z.GetIslandRemovalMode() for z in pours]
    for z in pours:
        z.SetIslandRemovalMode(pcb.ISLAND_REMOVAL_MODE_NEVER)
    refill(b)
    st = Stitcher(b, excl_boxes=[CO2_ISLAND], pour_layers=BOTH)
    for f in b.GetFootprints():
        if f.IsDNP() or f.IsBoardOnly():
            continue
        for pad in f.Pads():
            if pad.GetNetname() == 'GND' and pad.GetDrillSize().x == 0:
                q = pad.GetPosition()
                st.near(pcb.ToMM(q.x), pcb.ToMM(q.y), rmin=0.6, rmax=2.2, have=1.0)
    targeted = len(st.added)
    edge = 0                                  # fence just inside the lips (outer 1 mm is track/via-free)
    for x in [X0 + 1.9, X1 - 1.9]:
        y = 2.0
        while y <= H - 2.0:
            edge += st.add(round(x, 3), round(y, 3)); y += 2.0
    x = X0 + 2.0
    while x <= X1 - 2.0:
        edge += st.add(round(x, 3), 0.9) + st.add(round(x, 3), H - 0.9); x += 2.0
    field = st.grid(X0 + 3.0, 1.5, X1 - 3.0, H - 1.5, 3.0)
    for z, mode in zip(pours, modes):
        z.SetIslandRemovalMode(mode)
    refill(b)
    print(f'stitch: {targeted} targeted, {edge} edge, {field} field GND vias')


def islands(b):
    """Filled GND islands on both layers and which of them are joined (vias, GND THT pads, GND tracks)."""
    isl = []
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != 'GND':
            continue
        for layer in BOTH:
            if not z.IsOnLayer(layer):
                continue
            polys = z.GetFilledPolysList(layer)
            for k in range(polys.OutlineCount()):
                isl.append((layer, polys, k, abs(polys.Outline(k).Area())))
    parent = list(range(len(isl)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a

    def where(p, layer):
        return [n for n, (l, polys, k, _) in enumerate(isl) if l == layer and polys.Contains(p, k)]
    joints = [t.GetPosition() for t in b.GetTracks() if t.Type() == pcb.PCB_VIA_T and t.GetNetname() == 'GND']
    joints += [p.GetPosition() for f in b.GetFootprints() for p in f.Pads()
               if p.GetNetname() == 'GND' and p.GetDrillSize().x > 0]
    for q in joints:
        hit = where(q, pcb.F_Cu) + where(q, pcb.B_Cu)
        for n in hit[1:]:
            parent[find(n)] = find(hit[0])
    for t in b.GetTracks():
        if t.Type() == pcb.PCB_TRACE_T and t.GetNetname() == 'GND':
            hit = where(t.GetStart(), t.GetLayer()) + where(t.GetEnd(), t.GetLayer())
            for n in hit[1:]:
                parent[find(n)] = find(hit[0])
    return isl, find


def repair(b, rounds=4):
    """Put a via in every GND island that is not joined to the main plane, where the other layer is main."""
    total = 0
    for _ in range(rounds):
        refill(b)
        isl, find = islands(b)
        main = find(max(range(len(isl)), key=lambda n: isl[n][3]))
        # Centre inside the island and inside the main plane on the other layer is enough: the refill joins a
        # correctly spaced via to both pours. Clearances to other nets are still checked.
        st = Stitcher(b, excl_boxes=[], pour_layers=(), margin=0.0, pad_gap=0.2, via_gap=0.3, gnd_pad_gap=0.05)
        added = 0
        for n, (layer, polys, k, area) in enumerate(isl):
            if find(n) == main or area < pcb.FromMM(1.0) ** 2:
                continue
            other = pcb.B_Cu if layer == pcb.F_Cu else pcb.F_Cu
            bb = polys.Outline(k).BBox()
            x = pcb.ToMM(bb.GetX())
            done = False
            while x <= pcb.ToMM(bb.GetRight()) and not done:
                y = pcb.ToMM(bb.GetY())
                while y <= pcb.ToMM(bb.GetBottom()):
                    p = pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))
                    if polys.Contains(p, k) and any(find(m) == main and isl[m][0] == other and isl[m][1].Contains(p, isl[m][2])
                                                    for m in range(len(isl))):
                        if st.add(round(x, 3), round(y, 3)):
                            added += 1; done = True; break
                    y += 0.1
                x += 0.1
        total += added
        if not added:
            break
    refill(b)
    isl, find = islands(b)
    main = find(max(range(len(isl)), key=lambda n: isl[n][3]))
    left = [(pcb.ToMM(isl[n][1].Outline(isl[n][2]).BBox().Centre().x), pcb.ToMM(isl[n][1].Outline(isl[n][2]).BBox().Centre().y))
            for n in range(len(isl)) if find(n) != main]
    print(f'repair: {total} vias added; {len(left)} islands still separate', [(round(x, 1), round(y, 1)) for x, y in left][:12])


def main(mode):
    b = pcb.LoadBoard(str(BOARD))
    if mode == 'stitch':
        n = prune(b)
        print('pruned', n, 'dangling items')
    if mode == 'stitch':
        stitch(b)
    elif mode == 'repair':
        repair(b)
    pcb.SaveBoard(str(BOARD), b)


if __name__ == '__main__':
    main(sys.argv[1])
