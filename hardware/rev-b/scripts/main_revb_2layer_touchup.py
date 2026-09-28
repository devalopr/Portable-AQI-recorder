"""Final hand touch-up applied to the 2-layer router output (run with KiCad's Python after main_revb_2layer.sh).

TP3 (BOOT/GPIO9 test pad) ends up boxed in by the I2C lines at the left edge, with the display bus above it on the
front. If the router left it unconnected, it moves beside GPIO9's fixed back-side run next to R3. Then the stubs DRC reports as dangling are removed,
repeatedly; a stub stays if removing it would split its net (another track may land on it mid-segment).
Each pass runs in its own process (pcbnew cannot load a second board in one process).
"""
from pathlib import Path
import json, subprocess, sys, tempfile
import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pcb_edit import V, move, refill
from astar_finish import clusters

BOARD = Path(__file__).resolve().parents[1] / 'main/AQI_Main.kicad_pcb'
K = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'


def move_tp3():
    b = pcb.LoadBoard(str(BOARD))
    if len(clusters(b, '/BOOT_GPIO9')) == 1:        # the router reached TP3 where it is: leave it
        return
    move(b, 'TP3', 15.6, 57.7)
    t = pcb.PCB_TRACK(b)
    t.SetStart(V(15.6, 57.7)); t.SetEnd(V(15.6, 58.9)); t.SetWidth(pcb.FromMM(0.2)); t.SetLayer(pcb.B_Cu)
    t.SetNet(b.FindNet('/BOOT_GPIO9')); t.SetLocked(True); b.Add(t)
    pcb.SaveBoard(str(BOARD), b)


def clean(report):
    ids = {i['uuid'] for v in json.load(open(report))['violations'] if v['type'] in ('track_dangling', 'via_dangling')
           for i in v['items']}
    b = pcb.LoadBoard(str(BOARD))
    gone = 0
    for t in [t for t in b.GetTracks() if t.m_Uuid.AsString() in ids and not t.IsLocked()]:
        net = t.GetNetname()
        if len(clusters(b, net, skip=t)) <= len(clusters(b, net)):
            b.Delete(t); gone += 1
    refill(b)
    pcb.SaveBoard(str(BOARD), b)
    print(gone)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'clean':
        clean(sys.argv[2]); sys.exit()
    move_tp3()
    total = 0
    for _ in range(10):
        rep = tempfile.mktemp(suffix='.json')
        subprocess.run([K, 'pcb', 'drc', '--severity-all', '--refill-zones', '--format', 'json', '-o', rep, str(BOARD)],
                       capture_output=True)
        out = subprocess.run([sys.executable, __file__, 'clean', rep], capture_output=True, text=True).stdout.split()
        n = int(out[-1]) if out else 0
        total += n
        if not n:
            break
    print('removed', total, 'dangling stubs')
