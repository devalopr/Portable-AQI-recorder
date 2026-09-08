# Rev A battery-board circuit specification

Status: design input for schematic capture. This is a concrete starting circuit, not a released battery charger, safety certification, or fabrication BOM. The protected-cell and thermal assumptions must be checked against the selected 18650 holder and cell before build.

## Intended behavior

The board accepts 5 V power and USB 2.0 device data from an external USB-C receptacle, charges one standard 65 mm unprotected 18650 cell through an on-board DW01A/FS8205A protection stage, and produces a regulated 5 V rail for the AQI main board. It also exposes a general-purpose 3.3 V rail. The external USB D+/D- pair is carried directly to the main board through the internal harness; there is no USB hub in this revision. The main board remains the only USB device.

The internal cable is a ten-position JST GH harness. Its electrical allocation is:

| Pin | Net | Notes |
|---:|---|---|
| 1 | SYS_5V_A | 5 V output, parallel with pin 2 |
| 2 | SYS_5V_B | 5 V output |
| 3 | GND | power return |
| 4 | USB_D- | direct from external USB-C receptacle |
| 5 | USB_D+ | direct from external USB-C receptacle |
| 6 | GND | USB/I2C return |
| 7 | I2C_SDA | MAX17048 telemetry |
| 8 | I2C_SCL | MAX17048 telemetry |
| 9 | GND | I2C return |
| 10 | USB_HOST_PRESENT | 3.3 V logic indication of external VBUS |

Keep pins 4 and 5 adjacent, with ground pins 3 and 6 bracketing the pair in the harness. Use a short, twisted, controlled-impedance USB pair; ordinary ten-conductor ribbon cable is not assumed to work at full-speed USB. The GH family is a 1.25 mm pitch positive-latch connector. Initial orderable candidates are JST `SM10B-GH`/`S10B-GH-TB` (right-angle SMT header variants) and the matching crimp housing/contacts from the GH series; verify entry direction and exact mating parts against the enclosure before assigning the final footprint.

## Power and charging nets

Use these named nets in the KiCad schematic:

`USB_VBUS_IN` is the external USB-C VBUS after the connector. `BAT_RAW` is the holder positive terminal. `BAT_PROT` is the protected/reverse-polarity-corrected battery rail. `CHG_SYS` is the BQ24074 system output. `BOOST_5V` is the converter output and is the only source connected to internal pins 1/2. `GEN_3V3` is the generic regulated output.

### USB-C sink

Use a USB-C receptacle with USB 2.0 pins. Connect A4/B9 to `USB_VBUS_IN` and A1/A12 to board ground. Place one 5.1 kOhm 1% resistor from CC1 to ground and one from CC2 to ground (`RCC1`, `RCC2`, 0603). This advertises a sink and supports either cable orientation. Route A6/B6 together to `USB_D+`; route A7/B7 together to `USB_D-`, with ESD protection at the receptacle. Use a USB 2.0 low-capacitance protector such as `TPD2EUSB30A` (SOT-23-6) or an equivalent validated part; its exact MPN is still a BOM review item.

Place `CIN_USB = 4.7 uF, 10 V, X5R` plus `100 nF` at the charger IN pin. The BQ24074 IN input accepts 4.35–10.5 V and has input OVP; only a 5 V USB-C sink is intentionally exposed here.

### Cell connection and reverse protection

The holder shall accept a standard 65 mm **unprotected** 18650 cell and provide a board-side `CELL_NTC` connection. The board adds the protection circuit below. Use a board-mounted 10 kOhm NTC (nominal beta 3435 K, 1%) strapped to the cell, or a holder with an equivalent 10 kOhm thermistor. Do not populate a chargeable-cell design without a temperature sensor unless the charger TS network has been explicitly reviewed.

For Rev A reverse insertion protection, use a series Schottky diode `DREV` (SS34 or an equivalent 3 A, 40 V part) with **anode to BAT_RAW and cathode to BAT_PROT**. This intentionally spends approximately 0.3–0.5 V to guarantee that a reversed cell cannot be driven from the charger through a MOSFET body diode. Revisit an ideal-diode reverse-polarity circuit only after a validated dual-FET/controller design exists; a single P-MOSFET gate tied to ground is unsafe because the charger can drive the load side while a reversed cell is installed. This diode is supplemental reverse protection; it is not a replacement for a cell protection IC.

Add a dedicated 1-cell protector after the holder: `DW01A` plus dual back-to-back `FS8205A` N-MOSFET, with the cell-negative path switched and the charger/system return taken from the protected pack-negative node. Use the DW01A pin map `1=OD, 2=CS, 3=OC, 4=NC, 5=VCC, 6=GND`; use `470 ohm` from BAT_RAW to VCC, `100 nF` VCC-to-cell-negative, and `1 kOhm` between CS and protected pack-negative as starting values. Use FS8205A `1/8=D12 common drain, 2/3=S1, 4=G1, 5=G2, 6/7=S2`; connect the two gates to OD/OC and use cell-negative on S1 and protected pack-negative on S2. Verify the selected DW01A variant's delay/threshold and the MOSFET orientation against its manufacturer data before energizing the board. The series reverse-cell Schottky diode remains between BAT_RAW and BAT_PROT so a reversed cell cannot be driven from the charger through the protection FET body diodes.

### Charger / power path: BQ24074

Use `BQ24074RGT` (16-pin VQFN/RGT, 4.0 mm square) as the first schematic candidate. It provides a 4.2 V Li-ion charger, dynamic power path, input current limiting and battery temperature monitoring. The relevant pin-to-net map is:

| BQ24074 pin | Net/component | Connection |
|---:|---|---|
| 1 TS | `CELL_NTC` | 10 kOhm NTC (103AT-2 class) from TS to VSS, physically attached to the cell; do not add an unverified external bias divider |
| 2, 3 BAT | `BAT_PROT` | short, wide copper; `CBAT = 10 uF, 10 V X5R` to GND |
| 4 ~CE | `CHG_EN_N` | tie to GND for always-enabled charging; expose a test pad |
| 5 EN2 | `USB_ILIM_EN2` | drive from MCP23008 GP1; default LOW |
| 6 EN1 | `USB_ILIM_EN1` | drive from MCP23008 GP0; default LOW |
| 7 PGOOD | `USB_PRESENT_STATUS` | open drain; pull up to 3.3 V with 47 kOhm; optional test pad |
| 8 VSS | GND | ground plane and thermal pad |
| 9 CHG | `CHARGE_STATUS_N` | open drain; pull up to 3.3 V with 47 kOhm; optional test pad |
| 10, 11 OUT | `CHG_SYS` | short, wide copper; `CSYS = 22 uF, 10 V X5R` to GND |
| 12 ILIM | `RILIM = 1.50 kOhm, 1%` | to GND; approximately 1.03 A programmable input limit using TI's 1.55 kOhm factor |
| 13 IN | `USB_VBUS_IN` | `CIN_USB` close to pin |
| 14 TMR | `RTMR = 46.4 kOhm, 1%` to GND | TI's 6.25-hour fast-charge safety-timer example; revisit for the final cell capacity |
| 15 ITERM | `RITERM = 4.12 kOhm, 1%` to GND | TI's approximately 110 mA BQ24074 termination-current example |
| 16 ISET | `RISET = 1.13 kOhm, 1%` to GND | approximately 0.79 A fast-charge current using 890 A-ohm nominal factor |
| EP | GND | thermal pad, multiple vias |

The charge current and input current are deliberately below the device maximum to leave input power for the live system load. The exact cell capacity and USB-C source capability must determine whether approximately 0.8 A charge current is appropriate. Default `EN1=0, EN2=0` is USB100 (100 mA input limit). An MCP23008 on the shared I2C bus drives GP0/GP1 so firmware can select USB500 or resistor-programmed input limit only after source capability is known; add 100 kOhm pulldowns so reset state remains USB100. Do not leave either pin floating. Verify the BQ24074 TS, ITERM and TMR calculations against the final datasheet revision during schematic review. If charging while the 5 V boost is heavily loaded causes DPPM, reduce the charge current or input limit rather than bypassing the power path.

`CHG_SYS` is approximately 4.4 V when an adapter is present and follows the battery in supplement mode. It must feed the converters only; it must never be wired to USB_VBUS_IN or the USB-C VBUS pin.

## 5 V converter

Use `TPS61236P` in its 2.5 mm VQFN package as the 5 V boost candidate. TI documents a single-cell 2.3–5 V input to 5 V/2 A application. It has true shutdown disconnect and adjustable feedback. Use the following starting network, copied from the TI 5 V application and sized for layout review:

| Part | Starting value | Connection |
|---|---:|---|
| L5V | 1.0 uH, Isat >= 8 A, low DCR | CHG_SYS to SW |
| CIN5 | 10 uF, 10 V X5R plus 100 nF | CHG_SYS to PGND |
| COUT5 | 3 × 22 uF, 10 V X5R | BOOST_5V to PGND |
| R5V_TOP | 1.00 Mohm, 1% | BOOST_5V to FB |
| R5V_BOTTOM | 332 kOhm, 1% | FB to GND; gives about 5.0 V with the 1.244 V reference |
| CFF5 | 22 pF, C0G | across R5V_TOP, initially DNP until stability check |
| RDIS5 | 1 Mohm | BOOST_5V to INACT/required discharge-control node only if TI application requires it; do not invent a connection before pin review |

The exact TPS61236P symbol has nine pins (VQFN-HR/RWL); use the vendor pin table rather than the ten-pin TPS63031 symbol. At minimum: VIN to CHG_SYS, SW to L5V, VOUT to BOOST_5V, FB to the divider, EN to an always-on/enable net, AGND/PGND to ground, and CC/PG/INACT as required by the selected operating mode. The `CC` pin must be configured for a safe output-current limit, not left to an unreviewed default. This converter and its inductor need a compact hot loop and thermal copper. Treat 5 V/1 A as the initial system target; validate boost temperature and battery current with the SEN5x/SEN6x load.

## Generic 3.3 V converter

Use `TPS63031DSK` (2.5 mm VSON-10, fixed 3.3 V buck-boost) from `BAT_PROT` or `CHG_SYS`, with its own enable. This supports a regulated generic 3.3 V rail across a single-cell discharge. Starting connections follow the TI fixed-output application:

| Pin | Connection |
|---|---|
| VIN | `BAT_PROT` through `CIN3 = 10 uF, 10 V X5R` |
| VINA | `BAT_PROT` with 100 nF local bypass |
| L1/L2 | one 2.2 uH inductor between the two switch pins, Isat >= 2 A |
| VOUT | `GEN_3V3`, `COUT3 = 2 × 22 uF, 6.3 V X5R` |
| EN | `GEN3V3_EN`, 100 kOhm pulldown and test pad |
| PS/SYNC | GND for power-save operation, or strap high for forced-PWM after noise review |
| FB | VOUT for fixed 3.3 V variant |
| GND/PGND/EP | ground plane and thermal vias |

The generic output target is 3.3 V at up to roughly 0.5–0.8 A pending thermal measurement; do not advertise 1 A until tested. Provide a 2-pin 2.54 mm output header with 3V3/GND and a separate 5V/GND header. Include a resettable fuse or eFuse only if the generic-output use case demands user-proof short-circuit recovery; the converter's current/thermal protection is not a substitute for enclosure wiring protection.

## Battery fuel gauge

Use the 2 mm × 2 mm TDFN version `MAX17048G+T10` as the candidate. Its pin map is:

| Pin | Net |
|---:|---|
| 1 CTG | GND |
| 2 CELL | BAT_PROT (MAX17048 CELL is not internally connected but tie to the battery rail as recommended) |
| 3 VDD | BAT_PROT; `CGAUGE = 100 nF` to GND |
| 4 GND | GND |
| 5 ALRT | optional open-drain `GAUGE_ALERT_N` test pad; no main-board GPIO required |
| 6 QSTRT | GND |
| 7 SCL | I2C_SCL to GH pin 8 |
| 8 SDA | I2C_SDA to GH pin 7 |
| EP | GND if present |

Place the gauge on the protected battery rail before the converters. Pull SDA/SCL up to the main board's 3.3 V domain, not the battery board's `GEN_3V3`, so two independent regulator outputs are not tied. The main-board I2C switch/power-state design must prevent back-powering when the main board is off or the battery is absent. MAX17048 uses a model-based estimate rather than a current-sense coulomb counter; validate SOC against the selected cell, load profile and cutoff. Its host-side temperature compensation remains a firmware task.

## USB host-present sense

Derive `USB_HOST_PRESENT` from `USB_VBUS_IN` using `RHOST_TOP = 100 kOhm` from VBUS to `USB_HOST_PRESENT` and `RHOST_BOTTOM = 100 kOhm` to GND, followed by a 1 nF capacitor to GND at the harness source. This gives approximately 2.5 V at nominal VBUS, safely readable by a 3.3 V ESP32 input. It indicates external VBUS presence, which may be a charger rather than a data host; firmware must not treat it as USB enumeration or charging confirmation. Verify the main-board input protection and GPIO threshold before connecting it directly.

## Safety and unresolved items

The following must remain explicit review gates before producing a charging PCB:

1. Select the actual standard 65 mm 18650 cell and holder, including NTC attachment, maximum charge current and protection cutoff behavior.
2. Confirm the BQ24074 RGT thermal design and the final ITERM/CTMR values from the datasheet revision used for schematic capture.
3. Validate the TPS61236P pin/footprint and the exact TI reference network; its current-limit and CC/INACT configuration is not released by this document.
4. Validate 5 V boost thermal performance at 1 A, including the battery-board harness and GH contact temperature rise.
5. Add fuse/eFuse, reverse-current and ESD protection where the enclosure/user-accessible generic outputs require it.
6. Confirm USB D+/D- integrity through the chosen GH contacts and harness. The external USB-C cable remains the only upstream host connection; do not connect a second USB host without a reviewed mux/hub architecture.
7. Review battery insertion, reverse cell, charger-under-load, depleted-cell, unplug/replug, output-short and main-board power-switch behavior on a current-limited bench supply before connecting a real cell.

Primary references: [BQ24074 datasheet](https://www.ti.com/lit/ds/symlink/bq24074.pdf), [TPS61236P datasheet](https://www.ti.com/lit/ds/symlink/tps61236p.pdf), [TPS63031 datasheet](https://www.ti.com/lit/ds/symlink/tps63031.pdf), [MAX17048 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17048-MAX17049.pdf), and [JST GH series](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf).
