# BOM handoff — 2026-09-11

Continue from **review/engineering-bom.csv**, generated from **AQI_Battery_Cost_Revision.kicad_sch**. Source procurement metadata also lives in **design.json**. The older ../battery/review/engineering-bom.csv belongs to the older BQ25606/MAX17048 circuit and is not this revision's BOM.

## Applied

- Catalogue MPN, Manufacturer and LCSC fields filled for 58 priced placements: the revised ICs, JST GH connector, transistors, matched resistor values and capacitor candidates. Capacitor rows explicitly retain pending DC-bias qualification.
- Generic 18650 holder replaces Keystone branding in the cost-revision BOM. Exact manufacturer MPN remains unspecified; 15417 is a retailer SKU. User confirmed sourcing below INR30; costing uses INR30 conservatively.
- Holder dimensions from the main task: body 77.5 x 21.5mm, total terminal span 87mm, terminals 6.5mm wide. Existing footprint remains a placeholder and needs the measured-holder revision.
- USB-C replacements are explicit Candidate MPN/Candidate LCSC fields: J1 SHOU HAN TYPE-C 16PIN 2MD(073), C2765186; J7 SHOU HAN TYPE-C 6P, C456012. Original MPN/footprint fields remain together until the connector footprint changes are implemented. Their budget columns price the candidates.
- Every unresolved purchased component has a procurement-status explanation. DNP parts are retained for review; TP references are copper test pads with no separately purchased part.
- The cost-revision generator now reapplies procurement metadata and exports this CSV. For metadata-only refresh, run scripts/sync_cost_bom.py with KiCad bundled Python; do not regenerate a routed board.

## Cost baseline

1,000 boards, quantity tier based on total pieces of each MPN, INR96/USD planning rate. Catalogue stock/prices are LCSC-linked PCBParts results; they are not a completed JLC assembly quotation.

- Priced subset: INR231.2064 per board, 60 placements including two USB-C candidates.
- Generic holder allowance: INR30 per board.
- Partial subtotal: **INR261.21 per board**.
- Excluded: unresolved lines below, PCB, assembly/setup/attrition, programming, test, freight and taxes.

The HUSB305-01 candidate (C7471917, USD0.2033 at 1,000+) might replace the output CC controller and switch, saving INR59.88. It has not been applied or electrically approved. Even that conditional subtotal is INR201.33 before the unresolved parts and manufacturing. Do not present either subtotal as a completed factory cost.

## Remaining work for the main task

1. Complete the output controller/current-limit architecture and validate the increased load targets. U7 TUSB320 catalogue stock was only 392 against 1,000 required.
2. Implement and validate the selected USB-C and measured generic-holder footprints.
3. Resolve U5 exact Tani DW01A and Q2 Fortune FS8205A TSSOP-8 sourcing, three inductors, SW1 and RGB D1.
4. Resolve nine 22uF/16V/X7R/0805 capacitors and verify DC-bias performance of all power capacitors. No matching stocked 22uF result was found; no dielectric or package substitution has been applied.
5. Resolve R37 225k, R46 900k and R47 17k. Search rounded these to nearby values, which were not adopted. R12 retains exact 9.09k and R14 exact 82.5k/0.1%.
6. Regenerate and validate the assembly BOM after those design changes; obtain the full JLC quote.

Detailed prices and catalogue snapshot: [worksheet](../references/pricing-1000pcs-2026-09-11.md), [JSON](../references/pricing-1000pcs-2026-09-11.json).

This update only synchronizes procurement metadata and exports the BOM. Schematic connectivity, symbols, positions, and footprints are preserved. Routed boards and old fabrication/review exports were not regenerated.
