# Review tools and construction history

Use `refresh_review.py` to check/export the finished KiCad designs. It calls `verify_connectivity.py` to compare schematic and PCB pin nets with `design.json`. Neither tool saves or regenerates the source boards.

The other Python files are intermediate construction helpers, retained for traceability. Their outputs needed subsequent routing and engineering corrections. **Do not rerun them over the finished projects:** this can replace verified circuits, placements or routing. They are not a complete reproducible build of the final PCB files.

The final `.kicad_sch`, `.kicad_pcb`, `.kicad_pro`, project libraries and `validation.json` are the review baseline. The downloadable review archive contains the two review tools, not the historical construction helpers.
