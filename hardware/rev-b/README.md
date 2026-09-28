**Current boards (2026-09-27):** main board [main/](main/README.md) (USB-C input + Dupont battery-PWM header) and the battery board, now its own product in the private [18650-USB-C-UPS](https://github.com/devalopr/18650-USB-C-UPS) repo. The sections below describe earlier battery-board revisions.

# Compact standalone 18650 supply — Rev B engineering review

## Current BOM handoff — 2026-09-11

For continuing cost-reduction work, use [cost-revision/review/engineering-bom.csv](cost-revision/review/engineering-bom.csv) and [the sourcing handoff](cost-revision/BOM-HANDOFF.md). Procurement metadata is synchronized into the cost-revision schematic and design.json. The older battery/review CSV and the routed-board description below describe an earlier circuit.

The generic holder is costed at INR30 based on the user's under-INR30 source. The current priced subset including that allowance is INR261.21 per board at 1,000 boards; unresolved parts and manufacturing remain additional. This is not a complete production quotation.

Open **battery/AQI_Battery_Compact.kicad_pro**. This is the routed electrical revision; the older `AQI_Battery_Compact_Mechanical` file is only the superseded fit study. Rev A is unchanged.

## Size and interfaces

- **26.2 × 88 mm, two copper layers, 1.6 mm board.** Approximately 5.55 mm wider overall than the 20.65 mm holder model. Area is about 42% smaller than the old 44 × 90 mm board.
- Keystone **1042** surface-mount holder for a standard 65 mm cell, with its actual KiCad STEP model. Terminal pad span limits length; the input connector mounting geometry required the extra 0.5 mm over the initial fit study.
- Bottom input: Amphenol **12401610E4#2A**, centred on the board, with surface-mount signal contacts and through-hole shell anchors. Input USB data are passed to the optional GH interface.
- Top output: GCT **USB4135-GF-A**, power-only, all surface mount. TUSB320 attachment detection and TPS2552 switched/current-limited VBUS are included.
- J8/J9: unpopulated 2.54 mm through-hole rows on both sides of the output USB-C, each carrying 3.3 V, 5 V and GND (pins 1–3). Trim soldered wire ends flush on the holder side. Design load targets are 0.5 A at 5 V and 0.3 A at 3.3 V; USB and auxiliary loads share the converter budget. These are not bench-qualified ratings.
- JST GH host connector and MAX17048 fuel gauge retained for AQI compatibility. Neither is required to select charging current or operate the standalone indicator. R18/R19 I2C pullups are intentionally unpopulated when a host supplies pullups.

## Charge-rate selector

Recessed **C&K PCM13SMTR** three-position slide switch. Nominal labels: **500 mA / 1 A / 1.5 A**. Select with input power disconnected. The enclosure should expose a small tool-access opening; the PCB alone cannot enforce tweezers-only access.

BQ25606 switching charger; no MCU, firmware or ESP32 required. VSET is intentionally floating for nominal 4.208 V regulation. R36 (10 kΩ) provides a fixed normal-temperature bypass by default, so no thermistor is required. Optional TH1 is a Vishay NTCS0603E3103FLT 0603 SMD NTC (10 kΩ, B3435). Remove R36 when fitting TH1; never populate both. TH1 measures PCB temperature and does not provide direct cell-temperature monitoring.

R3 = 1.37 kΩ sets the low rate. R4 and R5 = 681 Ω form a tapped resistor ladder selected to ground by switch common pin 3. Calculated nominal rates are approximately **494 / 991 / 1488 mA**. An open selector contact falls back to low; overlapping adjacent contacts cannot add independent parallel branches beyond the high setting. Charger and resistor tolerances still apply.

For a nominal 0.5C target, 1 A corresponds to a 2000 mAh cell and 1.5 A to a 3000 mAh cell. Select within the actual cell manufacturer's charging limit. Cell size does not establish safe charge current. Full charging includes a taper phase and takes longer than two hours at 0.5C.

The input CC controller raises the input limit from nominal 0.50 A to about 1.42 A only when the source advertises at least 1.5 A. Charge current may be reduced by input power, concurrent loads or temperature. Legacy USB host enumeration/current-policy compliance remains a qualification item; this is not a certified universal USB product.

## RGB indicator

One small RGB LED, with 10 kΩ series resistors for dim operation. Autonomous comparator-based battery voltage bands: red below approximately 3.50 V; red + green between approximately 3.50 and 3.91 V; green above approximately 3.91 V. Blue is added during charging and follows the charger fault blink signal. Colours therefore blend while charging. This is an approximate voltage indication, **not a percentage gauge**. The optional MAX17048 supplies percentage data to an external I2C host.

## Validation and limits

- See `battery/review/erc.json`, `drc.json`, `connectivity.json` and `validation.json` for current results.
- All 273 intended electrical pins agree between the schematic netlist and PCB. ERC passes, routing has zero unconnected items and schematic parity passes.
- The dense charger escape includes approximately 2.8 mm total of 0.15 mm battery-net neck-downs; most of the repaired route uses 0.5 mm copper. Verify worst-case charging/discharging temperature rise and voltage drop before production.
- Ten unsuppressed mechanical DRC findings concern opposite-side holder courtyard overlap: four bare-header holes, two input shell anchors, two input locating holes and two selector locating holes. Bare holes are intentionally unpopulated; trim any wires flush. Verify input anchor/peg protrusion and holder clearance with actual parts before fabrication. These findings are not an electrical clearance waiver.
- The STEP includes the actual holder and library component models. RGB, TUSB320 and MAX17048 use explicitly named simplified body/fit models where installed library models were missing. They are not manufacturer-certified detailed CAD.
- Remaining release work: mechanical clearance sign-off, charge/boost thermal and load testing, USB attachment/current-limit behaviour, protection testing, optional temperature-sensing verification, and final exact passive BOM/availability review. Do not order production boards from this engineering package.

## Files

- `battery/AQI_Battery_Compact.kicad_pro`: editable KiCad project.
- `battery/review/AQI_Battery_Compact-fit-check.step`: Fusion fit-check assembly; use Upload/Open in Fusion, then compare to the enclosure.
- `battery/review/compact-holder.png` and `compact-rear.png`: review images.
- `battery/review/engineering-bom.csv`: engineering component list; unresolved passive selections are marked.

The scripts capture intermediate generation and repair operations. The checked-in PCB is the current routed source of truth; do not run the initial generator over it to update a small detail. Back up the working project before regeneration.
