# AQI recorder — Rev A engineering review

Implemented in KiCad 10. Main PCB: **44 × 80 mm**. Battery PCB: **44 × 90 mm**. Both use four copper layers, with In1.Cu reserved for ground. The checked KiCad files are the authoritative routed design.

| Project | Open in KiCad | Schematic PDF |
|---|---|---|
| Main board | [AQI_Main.kicad_pro](main/AQI_Main.kicad_pro) | [Main schematic](main/review/AQI_Main.pdf) |
| 18650 supply | [AQI_Battery.kicad_pro](battery/AQI_Battery.kicad_pro) | [Battery schematic](battery/review/AQI_Battery.pdf) |

This is an engineering review version. Fabrication release still requires the electrical, assembly and enclosure items below. Gerbers and an assembly-order package are intentionally not included.

Main-board front/rear PNGs now show all optional components, including CO₂ and e-paper parts. DNP flags remain intact in the BOM. Enable “Models marked DNP” in KiCad’s 3D viewer Appearance panel (shortcut D); this is a live viewer setting, independent of the saved PCB. Sensirion’s official SCD4x model and a simplified, dimensioned C&K switch model are included locally. Board previews do not include the external display, PM module, enclosure or battery holder; the complete enclosure assembly still needs checking. Right/left placement is specified from the front/display view, so the rear image is mirrored.

## Main board

- ESP32-C3-MINI-1-H4, at the lower left, with its integrated antenna facing the bottom edge and copper keepout on every layer (x = 0–15.7 mm, y = 73.8–80 mm).
- TFT flex wraps around the top edge to the rear **TE 1-84953-0, 10-way, 1 mm, top-contact** connector. Contacts face away from the PCB, as verified by the user. J5 is 9 mm lower than the earlier placement (origin y = 16.85 mm). The approach from the top edge is clear of components; verify the actual flex bend radius and connector engagement in the enclosure. The display body envelope is on Dwgs.User.
- Three front switches at x = 8, 22 and 36 mm, y = 66.25 mm. The power switch is on the right edge below the CO₂ island (origin x = 41.7 mm, y = 65.2 mm), with its actuator projecting outward. It disables the switched 5 V rail and downstream regulators.
- Bottom-right USB-C and adjacent front-mounted battery GH connector (origins x = 38.3 mm and 24.3 mm respectively). USB-C provides standalone power and ESP32 native USB. A TS3USB30E data switch selects the local port when local VBUS is present; otherwise it selects the internal link. TPS2116 isolates the two power sources. The data paths disconnect when neither host is present.
- TPS62160 regulators provide nominal 3.2 V for the MCU/TFT and about 3.33 V for SEN6x. The reduced core voltage gives the TFT supply margin below its 3.3 V upper limit.
- STCS05A current sink provides PWM backlight dimming; 1.5 Ω sets about 67 mA nominal. Validate brightness, current and backlight compliance against the actual display.
- Separate SEN5x and SEN6x connectors on the right edge, both rotated to put their actual mating openings outward to the right, prevent interchange of their 5 V and 3.3 V cables. Attach **one PM module**; the shared sensor address is 0x69.
- Optional SCD41 sits on a rear-right island (sensor origin y = 53 mm; island and both SEN connectors moved upward 4 mm), with two enclosed isolation slots, a 3 × 2 mm electrical bridge and two permanent 1.5 mm-wide outer-edge support tabs. Ground/power pours stop at the bridge; only four 0.15 mm traces cross it (power, ground, SDA and SCL). The outer tabs contain no copper on any layer; they add mechanical support but increase heat conduction through the laminate. Its TPS7A20 regulator stays on the main PCB; C16 decouples the sensor locally and C42 bypasses the regulator output. This reduces heat conduction; it does not eliminate self-heating or enclosure airflow effects. The CO₂ circuit remains DNP in the default assembly.
- GDEY037T03 e-paper connector J6 is at the opposite (left) upper edge, with its flex entry facing outward; its external boost circuit is provided as an alternate population. The TFT and e-paper share SPI, CS, DC and RESET: fit one display.

## Battery board

- MPD BH-18650-PC holder for a standard 65 mm unprotected cell.
- DW01A plus Fortune FS8205A implement cell overcharge, overdischarge and overcurrent protection. The selected FS8205A uses the **4.4 × 3 mm TSSOP-8** footprint.
- BQ24074 charger with power path. Attach a **10 kΩ cell-contact NTC** at J4; do not substitute a fixed resistor for the required temperature monitoring in an enclosed battery product.
- Charger defaults to USB100. MCP23008 at 0x21 controls EN1/EN2 and reads charge/input-present status. Configured charge-current ceiling is approximately 0.8 A; actual charging is bounded by input limit, load and thermal regulation.
- TPS61023 produces nominal 5.045 V and has a physical output-enable switch. TPS63031 provides the auxiliary 3.3 V output. Generic header design targets are 5 V / 0.5 A and 3.3 V / 0.3 A; these and the main board share the input/cell power budget and require load/thermal qualification.
- MAX17048 at 0x36 reports cell voltage and estimated state of charge through the shared I2C bus. Firmware reads SOC register 0x04 as an unsigned 8.8 percentage value; clamp the displayed value to 0–100%. Validate the gauge model and temperature compensation with the chosen cell.
- Battery-side I2C pullups R18/R19 are DNP when connected to the main board. The main board supplies 3.2 V pullups.
- Cell-negative is isolated from system GND by the protection FETs. Do not bypass this separation with a cable, mounting hardware or an external ground connection.
- The holder requires correct polarity. Reverse-cell insertion protection is not implemented. The 3.3 V control supply remains active when the 5 V output switch is off; remove the cell for long-term storage.

## Internal cable

Use **JST GH 10-way**, side-entry SM10B-GHS-TB headers and matching GHR-10V-S housings/appropriate GH crimp contacts. Wire pin 1 to pin 1; verify continuity rather than relying on an off-the-shelf cable's apparent orientation. Start with a harness no longer than 50 mm, using suitable 26–28 AWG contacts/wire and a twisted D+/D− pair where practical. Check USB operation with the final harness.

| Pin | Signal | Direction |
|---|---|---|
| 1, 2 | Regulated 5 V | Battery → main |
| 3 | GND | Common |
| 4 | USB D− | Bidirectional |
| 5 | USB D+ | Bidirectional |
| 6 | GND | Common |
| 7 | I2C SDA | Bidirectional |
| 8 | I2C SCL | Main → battery |
| 9 | GND | Common |
| 10 | External USB host present | Battery → main |

The battery USB-C is a sink/data port. USB CC termination stays at each external receptacle; CC is not carried through GH. The main board's internal GH input is not another USB-C receptacle and needs no additional CC termination. Both external ports are isolated by the main-board switching circuits.

SEN5x J3: 1 = 5 V, 2 = GND, 3 = SDA, 4 = SCL, 5 = GND, 6 = NC. SEN6x J4 uses a **custom 4-to-6 cable**: 1 = 3.3 V, 2 = GND, 3 = SDA, 4 = SCL; sensor pins 5/6 remain open. Do not use the battery GH cable for a sensor.

## Display population

Default handheld assembly: populate J5 and the backlight circuit; leave e-paper parts DNP. The optional SCD41 circuit is separately selectable.

E-paper assembly: populate J6, L3, Q3, D10–D12, R30/R31 and C30–C36/C38–C41. Keep R32 fitted for the reference circuit's BS-low setting. J7 is a high-level override: remove R32 before bridging J7. Leave J5 and the backlight circuit unpopulated. Confirm the exact panel revision, flex thickness/contact orientation and BS setting against the purchased panel before assembly. The vendor pin table and reference drawing disagree about BS; this is a release item, not a resolved assumption.

The ESP32 pin allocation supports ESPHome. The exact GDEY037T03/UC8253 driver has not been validated in ESPHome; GxEPD2 has a panel driver, but using that Arduino driver does not by itself provide an ESPHome component. The repository's current prototype firmware also needs the Rev A GPIO map, MCP23008 buttons and fuel-gauge integration. See [firmware integration](firmware/README.md).

## Checks and release items

The final review includes KiCad ERC, DRC with schematic parity, an independent comparison of every connected pin against design.json, schematic PDFs, board renders and engineering BOMs. See [validation.json](validation.json) for actual results and checked file hashes. A clean DRC confirms geometry/connectivity rules; it does not validate a circuit's analogue performance or the enclosure.

Before fabrication release:

1. Finish the enclosure CAD: TFT bend radius, connector latch access, button caps/travel, PCB retention, sensor airflow and battery-holder clearance. No PCB mounting holes are included; the current outline assumes enclosure rails/retainers. Support the CO₂ island without a conductive metal bridge or force on the sensor. Check the isolation-slot tool radius and island strength with the fabricator; provide local enclosure support clear of the sensor opening.
2. Qualify the integrated antenna in the final enclosure. The TFT body spans x = 0.64–43.36 mm, y = 1.5–62.46 mm. The revised antenna spans approximately x = 2.4–15.6 mm, y = 74.1–79.5 mm, so it no longer lies behind the display. The nominal display-to-antenna gap is about 11.6 mm; the button and adjacent GH connector metal are closer. This 44 × 80 mm layout does **not** provide [Espressif's recommended 15 mm clearance in all directions](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html#general-principles-of-pcb-layout-for-modules-positioning-a-module-on-a-base-board). Keep the cell, sensor bodies, cables, fasteners and enclosure metal away from the antenna. Measure Wi-Fi/BLE performance with the final LCD or e-paper assembly; copper keepouts alone do not establish RF performance. The integrated-antenna module is retained as requested; no external antenna substitution is made.
3. Qualify USB current and inrush. Standalone sensing requires a suitable 5 V supply (start with a rated 1 A or higher adapter). The main board does not detect Type-C advertised current. The battery board starts at 100 mA; firmware must establish the allowed source current before selecting 500 mA or resistor-programmed mode. Do not assume every host port permits 1 A. Verify boot/measurement with the battery absent and depleted, plus both-port plug/unplug transitions.
4. Review exact MLCC/inductor ordering codes, effective capacitance under DC bias, component substitutions and assembly availability. The CSVs are engineering BOMs, not approved JLCPCB assembly BOMs. In particular, verify the e-paper flying capacitor at its operating voltage.
5. Check battery protection thresholds against the selected cell, charge/discharge operation, cell NTC limits, output overload behaviour and temperatures in the enclosure. Review exposed-pad thermal vias and stencil/tenting with the assembler.
6. Validate CO₂ temperature offset with Wi-Fi, the display and PM sensor operating. Couple the CO₂ opening to ambient air and shield it from PM fan turbulence. Validate USB signal quality, regulator transients, backlight PWM, e-paper power sequencing/BS setting and the exact ESPHome display driver on hardware.

## Sources and reproducibility

The selected circuits were checked against manufacturer datasheets retained under references/datasheets. Main sources include [Espressif module documentation](https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.html), [TI BQ24074](https://www.ti.com/lit/ds/symlink/bq24074.pdf), [TI TPS61023](https://www.ti.com/lit/ds/symlink/tps61023.pdf), [ADI MAX17048](https://www.analog.com/media/en/technical-documentation/data-sheets/max17048-max17049.pdf), and the [Good Display reference document](https://ecksteinimg.de/Photo/GD03042/GDEY037T03-T02.pdf?_t=1768267937). [GxEPD2](https://github.com/ZinggJM/GxEPD2) lists the exact panel; the [ESPHome UC8253 discussion](https://github.com/orgs/esphome/discussions/3504) documents the integration gap.

Run `python3 scripts/refresh_review.py --render` with KiCad 10 installed to refresh checks, PDF/SVG/BOM exports and native board PNGs from the current KiCad files. The script accepts `--cli` and `--pcb-python` overrides; the latter must provide KiCad's pcbnew module. It does not regenerate the boards. Early research and construction helpers are retained for traceability; rebuilding from their intermediate inputs can erase or replace the manually finished routing.
