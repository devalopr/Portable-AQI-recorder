# Rev A main-board circuit specification

Status: implementation input for KiCad schematic capture, 2026-09-07. This is a circuit and pin-contract specification; it does not release a PCB or fabrication BOM. Net names below are the names the schematic should use.

## USB and 5 V input selection

Use `U_PWR1 = TPS2116DRL` (TI SOT-583-8, KiCad symbol `Power_Management:TPS2116DRL`, footprint `Package_TO_SOT_SMD:SOT-583-8`). The TI pin table is: 1 GND, 2/7 VOUT, 3 VIN1, 4 PR1, 5 MODE, 6 VIN2, 8 ST. VIN1 is the priority input when PR1 is high; MODE tied to VIN1 selects priority mode. The device accepts 1.6–5.5 V, provides reverse-current blocking, and is rated for 2.5 A continuous current. Source: [TPS2116 datasheet](https://www.ti.com/lit/gpn/TPS2116), section 5 and sections 6–8.

Connect:

| U_PWR1 pin | Net | Function |
|---:|---|---|
| 1 | GND | Ground |
| 2, 7 | `SYS_5V` | Mux output, short and wide copper |
| 3 | `USB5V_LOCAL` | Main USB-C VBUS after input protection/current-limit provisions |
| 4 | `USB5V_LOCAL` through 10 kΩ (or direct if the exact symbol/reference design permits) | `PR1=high`, local port priority |
| 5 | `USB5V_LOCAL` | Priority mode |
| 6 | `USB5V_INTERNAL` | JST GH internal 5 V input |
| 8 | `PWR_MUX_ST` | Optional open-drain status; 10 kΩ pull-up to 3V3 |

The TPS2116 data sheet says ST is low when VIN1 is not being used. Do not use ST as the battery-board host-present indication; carry that indication on the tenth GH contact as `INT_HOST_PRESENT`.

Local USB data has priority only when a local VBUS is present. For the USB mux select logic, use `LOCAL_VBUS_PRESENT` from a VBUS divider/comparator or an approved USB-C power controller and form:

`USB_SEL_INTERNAL = INT_HOST_PRESENT AND NOT LOCAL_VBUS_PRESENT`.

That signal drives the USB switch S input. This avoids selecting an internal host while the local USB-C host is attached. A small 3.3 V logic gate is required; do not connect `INT_HOST_PRESENT` directly to S if local priority is required.

## USB data mux

Use `U_USB1 = TS3USB30EDGSR` (TI VSSOP-10, KiCad symbol `Interface_USB:TS3USB30EDGSR`, footprint `Package_SO:TSSOP-10_3x3mm_P0.5mm`). The current TI E revision has the following VSSOP pin map: 1 S, 2 D1+, 3 D2+, 4 D+, 5 GND, 6 D−, 7 D2−, 8 D1−, 9 OE, 10 VCC. D is the common side; D1 and D2 are the two switched sides. S low selects D1, S high selects D2; OE high disconnects all paths. Source: [TS3USB30E datasheet](https://www.ti.com/lit/ds/symlink/ts3usb30e.pdf), section 4 and truth table 7-1.

Use the following net assignment:

| U_USB1 pin | Net | Function |
|---:|---|---|
| 1 | `USB_SEL_INTERNAL` | High selects internal path D2 |
| 2 | `USB_DP_LOCAL` | Local USB-C D+ |
| 3 | `USB_DP_INTERNAL` | GH D+ |
| 4 | `USB_DP_MCU` | ESP32 GPIO19/module pad 27 |
| 5 | GND | Ground |
| 6 | `USB_DM_MCU` | ESP32 GPIO18/module pad 26 |
| 7 | `USB_DM_INTERNAL` | GH D− |
| 8 | `USB_DM_LOCAL` | Local USB-C D− |
| 9 | `USB_MUX_OE_N` | Low enables mux; default pull-up to 3V3 and firmware/host-presence-controlled pull-down |
| 10 | `3V3` | Supply; 2.7–4.3 V operating range |

Place the mux close to the ESP32 and keep each D+/D− branch short, symmetric, and on a continuous reference plane. The TS3USB30E supports partial power-down but does not replace USB-C attach/current control or ESD protection. Provide ESD protection at the USB-C receptacle and keep series-resistor footprints available at the ESP32 interface.

## ESP32-C3 module

Use `ESP32-C3-MINI-1-H4X` if the 105 °C H4 variant is required; the older `ESP32-C3-MINI-1-H4` is marked NRND in Espressif’s current v2.2 datasheet. Use the official 53-pad land pattern from Figure 11-1: 13.2 × 16.6 mm module, 48 perimeter pads and the exposed/ground pad pattern as specified by Espressif. No stock KiCad symbol/footprint matching the exact MINI module was found in the installed library; create a project-local symbol and footprint directly from the official pin table and land-pattern figure, with the antenna keepout included on the PCB.

Required module connections:

| Module pad | Module name | Net |
|---:|---|---|
| 3 | 3V3 | `3V3` |
| 8 | EN | `MCU_EN` with the Espressif RC/reset network; never float |
| 12 | IO0/GPIO0 | `I2C_SDA` |
| 13 | IO1/GPIO1 | `I2C_SCL` |
| 18 | IO4/GPIO4 | `LCD_SCLK` |
| 19 | IO5/GPIO5 | `LCD_DC` |
| 20 | IO6/GPIO6 | `LCD_MOSI` |
| 21 | IO7/GPIO7 | `LCD_RESET` |
| 16 | IO10/GPIO10 | `LCD_CS` |
| 26 | IO18/GPIO18 | `USB_DM_MCU` |
| 27 | IO19/GPIO19 | `USB_DP_MCU` |
| 30 | RXD0/GPIO20 | `EPAPER_BUSY` or service RX, mutually exclusive |
| 31 | TXD0/GPIO21 | service TX/spare |

Keep GPIO2, GPIO8 and GPIO9 available for boot strapping/service access. Source: [Espressif ESP32-C3-MINI-1 datasheet](https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.html), sections 3, 8, 10 and 11.

## Core 3.3 V buck

Use `U_CORE1 = TPS62160DGKR` (VSSOP-8, `Package_SO: VSSOP-8_3.0x3.0mm_P0.65mm`). The exact pin map is 1 PGND, 2 VIN, 3 EN, 4 AGND, 5 FB, 6 VOS, 7 SW, 8 PG. Use the adjustable version from 5 V to 3.3 V; the fixed 3.3 V variant is TPS62162 and should be considered if sourcing is better. Source: [TPS6216x datasheet](https://www.ti.com/lit/ds/symlink/tps62160.pdf), section 6.

Connect VIN to `SYS_5V` with the data-sheet input ceramic capacitor, EN to `MAIN_RAIL_EN`, PG to an optional 3V3 pull-up/status net, SW through the selected 2.2–3.3 µH inductor to `3V3`, and VOS to the regulated output sense point. For TPS62160, use the 0.8 V reference and a divider of 316 kΩ top / 100 kΩ bottom as the initial 3.3 V target; verify the final resistor values against the data-sheet layout/reference design. FB is the divider midpoint. Use the manufacturer-recommended inductor current rating and output capacitance; the data sheet lists 2.2 µH parts around 1.3–1.9 A as examples.

## Quiet SCD4x rail

Use `U_SCDLDO1 = TPS7A2033PDBVR` (SOT-23-5, `Package_TO_SOT_SMD:SOT-23-5`) as the optional quiet 3.3 V rail. The device provides 300 mA, 7 µVrms noise and high PSRR; it is suitable for the SCD4x peak-load budget when thermal dissipation is checked. Use the DBV pin assignment from the TI data sheet: IN, GND, EN, NC, OUT; confirm symbol pin numbering before capture. Source: [TPS7A20 product/datasheet](https://www.ti.com/lit/ds/symlink/tps7a20.pdf).

Connect input to `3V3`, output to `SCD_3V3`, EN to `SCD_RAIL_EN` with the device’s internal enable pulldown, NC left open, and place the required 1 µF minimum input/output capacitors at the pins. Keep SCD_3V3 and its return physically away from the buck SW node, LCD backlight and ESP32 antenna.

## Backlight current and PWM

Use `U_BL1 = STCS05ADR` (SO-8, `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`) as a simple constant-current sink with PWM. Pin names are VCC, DRAIN, PWM, EN, DISC, FB, SLOPE and GND; verify the exact SO-8 pin numbers against the ST symbol/datasheet before capture. Feed VCC from `SYS_5V`, connect EN high through the main rail enable, PWM to ESP32 GPIO3 (`LCD_BL_PWM`), and connect the display backlight cathode net to DRAIN. Set the initial total current to 80 mA with `R_FB = 100 mV / 80 mA = 1.25 Ω` (use 1.24 Ω, 1%, after thermal and brightness testing). Leave DISC unused only if the diagnostic is intentionally omitted; otherwise pull it up as shown in the data sheet. SLOPE may be left open for fastest edge or populated with a small capacitor after EMI testing. Source: [STCS05A datasheet](https://www.st.com/resource/en/datasheet/stcs05a.pdf).

The panel drawing describes four parallel white LEDs. Do not assume bare parallel dies share current safely. Confirm that the actual LCD module contains per-branch ballast resistors; if it does not, add one ballast resistor per LED branch or use a driver topology intended for independently ballasted parallel branches. Check `P=(5 V−VLED−VFB)×80 mA` at the actual panel forward voltage and provide copper for the SO-8 thermal load.

## Button expander

Use `U_IO1 = MCP23008-xSO` (SOIC-18, `Package_SO:SOIC-18_3.9x9.9mm_P1.27mm`) at I2C address 0x20: connect A0, A1 and A2 to GND. The Microchip pin contract is SCL=1, SDA=2, A2=3, A1=4, A0=5, RESET=6, NC=7, INT=8, VSS=9, GP0..GP7=10..17, VDD=18. Source: [MCP23008 data sheet](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23008-and-MCP23S08-Data-Sheet-DS20001919.pdf).

Connect SCL/SDA to `I2C_SCL`/`I2C_SDA`, VDD to `3V3`, VSS to GND, RESET to `MCU_EN` with a local pull-up, and use GP0, GP1 and GP2 as active-low button inputs with pull-ups enabled or external 10 kΩ pull-ups to 3V3. Connect each button from GPx to GND. Leave GP3..GP7 as named spare GPIOs with test pads; leave INT unconnected for the polling design or route it to a future MCU interrupt pad. Do not leave the MCP23008 address pins floating.

## Unresolved before schematic release

The exact LCD backlight electrical topology, final module order code/H4X availability, final antenna keepout relative to the enclosure, local USB-C protection/controller selection, and the mechanical orientation of the 10-position JST GH remain open. The TS3USB30E data switch also needs the selected `USB_SEL_INTERNAL` logic gate and a defined power-up default for `OE`.
