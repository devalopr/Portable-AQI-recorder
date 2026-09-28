#!/bin/zsh
# Close out a routed 2-layer board: join GND pockets, reroute whatever that displaced, repeat until clean.
set -e
cd "${0:A:h}"
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
B=../main/AQI_Main.kicad_pcb
D=../main/review/routing/loop-drc.json
quiet() { grep -v "leak\|assert\|Debug" || true }
for round in 1 2 3 4; do
  $PY main_revb_2layer_finish.py repair 2>&1 | quiet
  $PY astar_finish.py gnd $B 2>&1 | quiet
  for pass in 1 2 3; do
    $K pcb drc --severity-all --refill-zones --format json -o $D $B > /dev/null
    open=$(python3 -c "import json;print(len(json.load(open('$D'))['unconnected_items']))")
    echo "round $round pass $pass: $open unconnected"
    [ "$open" = 0 ] && break
    $PY astar_finish.py $B $D 2>&1 | quiet | grep -E "FAILED|rip-up" || true
  done
  [ "$open" = 0 ] && break
done
