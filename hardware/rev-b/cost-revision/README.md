# Cost-reduction schematic study

Current sourcing/BOM continuation: [BOM-HANDOFF.md](BOM-HANDOFF.md). The [engineering BOM](review/engineering-bom.csv) now exports procurement metadata and explicit candidate/unresolved statuses from this schematic. The generic holder allowance is INR30; footprint implementation remains pending.

This directory is an electrical study, not a replacement routed PCB or fabrication release. Open `AQI_Battery_Cost_Revision.kicad_pro`. The earlier battery board and main board remain separate.

## Accepted product requirements

- Two layers, compact single 65 mm unprotected 18650 holder with PCB protection.
- USB-C input and output, three-position 0.5/1/1.5 A nominal charging selector.
- Approximate voltage-derived battery percentage is accepted (2026-09-11). PWM is now selected for the standalone product: GH7 plus a solder pad, open drain, 100Hz, 10–90% HIGH duty. GH8 is reserved/NC. See ../firmware/telemetry/README.md.
- A small MCU replaces the MAX17048 and comparator/reference RGB circuit. Charging and protection remain hardware-controlled.
- Revised output target: 5V/2A and 3.3V/1A with a shared boost power budget. Both maxima are not simultaneous. The power stage remains unqualified for these targets; a passing ERC does not establish output-current capability.

## Implemented schematic changes

- ETA6003Q3Q switching charger with system power path, replacing BQ25606.
- ISET1: 2k base with a tapped 1k+1k branch selected by the existing small switch. Nominal settings 0.5/1/1.5 A; open contacts select 0.5 A.
- ISET2: 2k, selected when a higher-current USB-C source is not detected.
- HUSB320-BA000 input CC detector in GPIO sink mode, with 900k PORT pull-down.
- SY6280AAAC hardware total input limiter. Nominal low/high limits about 0.400/1.185 A. Allowance for current-limit tolerance is intentional. This limits attainable charge current, particularly near full charge or with a load. **A higher-current input stage is still required to meet the new output specification.**
- SY8089A1AAC 3.3 V buck powered from BOOST_5V. Divider 225k/49.9k sets approximately 3.305 V. This increases the required 5 V converter output power.
- CH32V003F4P6: PC1 drives the Q5 open-drain PWM output; PC2 is unused; battery/input voltage sensing on PD2/PD3; RGB on PD4/PD5/PD6; SWIO and reset test pads. PWM transmitter and receiver modules are implemented and checked; battery application integration and board-specific ADC calibration are outstanding.
- The output Type-C controller remains TUSB320LAI; cheaper HUSB320 source-mode reset-current behavior has not been cleared for substitution.

## Parts screened out

- IP2312U_VSET: minimum resistor-programmed current approximately 0.8 A; exceeding its allowed resistor range returns to 2.1 A default. Does not satisfy the required 0.5 A setting.
- CW2015: lower-cost dedicated gauge, but battery-profile provisioning/qualification complicates support for replaceable generic cells. Not fitted; user accepted the MCU voltage estimate.
- HUSB305: minimum advertised source-current modes do not fit the previous low-power output budget. Reassess against the newly increased output rating, not as a pin-for-pin replacement.

## Power budget for the new requirement

5 V × 2 A = **10 W total output**. At an illustrative 90% efficiency this requires about **3.0 A at 3.7 V**, rising to **3.7 A at 3.0 V** from the cell. These are sizing estimates, not measured performance. Cell, contacts, protection and converter must support the low-cell current continuously.

Full 1.5 A charging near 4.2 V adds 6.3 W at the cell. Full output plus full charging requires more than 16.3 W input before losses; a 5 V/3 A input cannot sustain both. Reduce charging under load.

## Reference module inspected

User photo IMG_3240.heic shows an IP5306, a 2R2-marked inductor, ceramic capacitors, four indicator LEDs, battery solder pads and a button connection. Exact IC variant, capacitor values and backside circuitry are not established by this photo. The integrated charger/boost/indicator architecture is worth evaluating for cost reduction, but is not yet selected for our schematic.

The Roboman listing advertises 5 V/2 A, ₹59 including GST and auto-off below 50 mA. Its charge-current and cutoff-voltage claims need checking against the exact populated IC variant. Preserve low-load operation in our product, and verify selectable charging currents and safe startup before choosing an integrated alternative. Our approximate PWM battery telemetry and RGB requirements remain. The 3.3V/1A branch consumes approximately 0.73A from the 5V boost at an assumed 90% buck efficiency, leaving about 1.2A for external 5V loads with margin.

Reference: https://roboman.in/product/type-c-usb-5v-2a-step-up-boost-converter-with-usb-charger-non-solder/

## Review status

Schematic ERC: zero errors/warnings after reflow. Exported netlist was compared to every intended non-null component connection with no mismatches. These checks do not establish thermal ratings, USB compliance, holder fit, or charging performance. Existing Rev B STEP/ZIP files predate this study and must not be described as exports of this circuit.

Outstanding: revised high-current architecture, exact passive/connector procurement, holder terminal dimensions and underside clearance, PCB layout/routing, MCU firmware, load/thermal/protection tests, and assembled production quotation. No final selling price has been established.

## Primary documentation

- ETA6003 manufacturer datasheet: https://files.waveshare.com/upload/3/3f/ETA6003.pdf
- SY8089A1: https://www.silergy.com/download/downloadFile?ftype=note&id=3756&type=product
- SY6280/A: https://www.silergy.com/download/downloadFile?ftype=note&id=4369&type=product
- HUSB320: https://www.hynetek.com/uploadfiles/site/219/news/4ded9a63-401a-4cf0-a009-d45e4f8b8075.pdf
- CH32V003: https://www.wch-ic.com/products/CH32V003.html

## PWM implementation

Q5 (2N7002), R49 (100k gate pulldown) and TP8 implement host-voltage open-drain PWM. Battery-side I2C pullups R18/R19 are removed. The corresponding main schematic is in ../main-pwm. Protocol and firmware status are documented in ../firmware/telemetry/README.md. The earlier routed battery board remains unchanged.
