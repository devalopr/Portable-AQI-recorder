#!/bin/zsh
# Rev B main board, 2-layer / 76 mm: placement -> Freerouting -> A* finish -> ground stitching -> checks.
# Needs KiCad 10, a Java 25+ runtime and freerouting-2.4.1.jar (FREEROUTING, default ~/Applications/freerouting/).
set -e
setopt null_glob
cd "${0:A:h}"
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
JAVA=${JAVA:-/opt/homebrew/opt/openjdk/bin/java}
FR=${FREEROUTING:-$HOME/Applications/freerouting/freerouting-2.4.1.jar}
MAIN=../main
R=$MAIN/review/routing
quiet() { grep -v "leak\|assert\|Debug" || true }

$PY main_revb_2layer.py place 2>&1 | quiet
rm -f $R/AQI_Main.ses
$JAVA -Djava.awt.headless=true -jar $FR -de $R/AQI_Main.dsn -do $R/AQI_Main.ses -mp 100 \
    --gui.enabled=false --router.optimizer.enabled=false > $R/freerouting.log 2>&1
echo "freerouting: $(grep -o '([0-9]* items still unconnected)' $R/freerouting.log | tail -1)"
$PY main_revb_2layer.py import 2>&1 | quiet
$K pcb drc --severity-all --refill-zones --format json -o $R/after-router-drc.json $MAIN/AQI_Main.kicad_pcb > /dev/null
$PY astar_finish.py $MAIN/AQI_Main.kicad_pcb $R/after-router-drc.json 2>&1 | quiet
$PY main_revb_2layer_finish.py stitch 2>&1 | quiet
# stitching prunes dangling stubs; finish anything that left open, then join the remaining GND islands
for pass in 1 2 3; do
  $K pcb drc --severity-all --refill-zones --format json -o $R/after-stitch-drc.json $MAIN/AQI_Main.kicad_pcb > /dev/null
  $PY astar_finish.py $MAIN/AQI_Main.kicad_pcb $R/after-stitch-drc.json 2>&1 | quiet
done
$PY main_revb_2layer_finish.py repair 2>&1 | quiet
$PY astar_finish.py gndfix $MAIN/AQI_Main.kicad_pcb 2>&1 | quiet
# anything still open: route it, displacing other copper only if everything displaced reconnects
$K pcb drc --severity-all --refill-zones --format json -o $R/final-open.json $MAIN/AQI_Main.kicad_pcb > /dev/null
open_nets=($(python3 -c "
import json,re;d=json.load(open('$R/final-open.json'));s=set()
for u in d['unconnected_items']:
  for i in u['items']:
    m=re.search(r'\[([^\]]+)\]',i['description'])
    if m and m.group(1)!='GND': s.add(m.group(1))
print(' '.join(sorted(s)))"))
[ ${#open_nets} -gt 0 ] && $PY astar_finish.py verified $MAIN/AQI_Main.kicad_pcb $open_nets 2>&1 | quiet
$K pcb drc --schematic-parity --severity-all --refill-zones --format json -o $MAIN/review/drc.json $MAIN/AQI_Main.kicad_pcb | grep Found
$PY main_revb_2layer_touchup.py 2>&1 | quiet
$PY main_revb_2layer.py sync 2>&1 | quiet
$K pcb drc --schematic-parity --severity-all --refill-zones --format json -o $MAIN/review/drc.json $MAIN/AQI_Main.kicad_pcb | grep Found
