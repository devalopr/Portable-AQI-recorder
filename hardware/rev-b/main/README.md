# AQI main board — Rev B

Open `AQI_Main.kicad_pro` in KiCad 10. This board mates with the IP5310 battery board, which now lives in its own private repo, [18650-USB-C-UPS](https://github.com/devalopr/18650-USB-C-UPS). It starts from the routed Rev A board; `../../rev-a/main` is unchanged, and `../main-pwm` (schematic only, still with the GH connector) is superseded.

**47 × 76 mm, two layers, 1.6 mm.** This is 4 mm shorter and 3 mm wider than Rev A, and two layers instead of four. The previous 4-layer, 80 mm version is kept in `review/rev-b-4layer-80mm/` (board, `design.json` and its cost).

Changes in the 2-layer, 47 × 76 mm re-layout:

- **Wider, with mounting lips.** The board grew 1.5 mm on each long side, from 44 to 47 mm, for routing room. Board coordinates keep the Rev A origin, so the board now spans x = −1.5 to 45.5 mm. The outer 1 mm on each side (x = −1.5 to −0.5 and 44.5 to 45.5 mm) is a lip for clamping the board in the case. It carries only the ground pour: no tracks or vias. SW4 moved out 1.5 mm with the edge.

- **Shorter bottom.** Everything below the buttons moved up 4 mm and the bottom edge was cut to match:
  - the ESP32 module, which keeps its antenna at the edge, and its supply caps;
  - USB-C and D1;
  - the J2/J8 headers.

  The limit is USB-C: its shield legs pass through the board and must stay clear of the OK button's pads.
- **CO₂ on top.** The CO₂ island is now at the top of the right column (y = 21–35 mm, under J5), above SEN5x and SEN6x. It is fed through its bottom-right tab instead of the middle tab (see Layout). Set `ISLAND_DY = 0` in `main_revb_2layer.py` to go back to the island at the bottom of the column.
- **Sensor connectors.** J3 (SEN5x, y = 37–49 mm) and J4 (SEN6x, y = 49.8–59.4 mm) sit below the island, 6 mm in from the original right edge. Their mouths face the edge from x = 37.5 mm, leaving 8 mm on the board for the GH plug and for the cable to bend down before it reaches the case.
- **E-paper through an adapter.** The on-board e-paper boost circuit and its 24-pin FPC connector are gone. An unfitted 8-pin header J6 takes their place (see below).
- **Two layers.** The front copper, where only the buttons sit, carries ground plus as few signals as possible. A few critical nets are laid first as fixed routes (see Layout), and the rest are routed around them.

## Front: display and buttons

The front carries only the display and the three buttons. Everything else, including USB-C, is on the back.

- **Display.** A 2.4-inch 240 × 320 ST7789 panel with a 10-way, 1.0 mm-pitch flex.
  - **Size:** 42.72 × 60.26 × 2.5 mm, with a 36.72 × 48.96 mm active area (common datasheet values; you measured about 42.5 × 60 × 2.5 mm).
  - **Position:** centred in the Rev A display envelope, which spans x = 0.64–43.36 mm, y = 1.5–62.46 mm (board origin top-left, seen from the front). The panel itself spans y = 1.85–62.11 mm.
  - **Height:** it sits on 0.2 mm tape, so its front face is 2.7 mm above the board.
  - **Flex:** exits at the top, wraps over the top edge (about 1.5 mm past it) and runs into J5 on the back. The active area therefore sits toward the buttons, and firmware rotates the image.
  - **In the files:** the board-only footprint DS1 carries the panel's 3D model and outline. It isn't in the BOM or the placement file. The envelope is also drawn on Dwgs.User, labelled "TFT DISPLAY BODY (FRONT)".
  - The active-area offsets (3.0 mm at the sides, 3.2 mm at the far end, 8.1 mm at the flex end) and the flex path are typical values, not from your panel's drawing. Check them against the part you buy.
  - Nothing is placed on the front under the panel.
- **Buttons.** SW1 LEFT, SW2 OK and SW3 RIGHT sit in one row directly below the display:
  - centres at x = 9, 22 and 35 mm, y = 66.25 mm;
  - an even 13 mm pitch, centred on the board and the display (x = 22);
  - XKB TS-1187A: 5.1 × 5.1 mm body, 1.5 mm tall;
  - bodies at y = 63.7–68.8 mm, about 1.2 mm below the display edge.

  The switch tops (1.5 mm) are 1.2 mm below the display face (2.7 mm), so the enclosure needs button caps or plungers that reach the front face. The silkscreen labels L / OK / R are under each button.
- **3D models.** They are all in `lib/3d/` and the footprints point at them through `${KIPRJMOD}`; see `lib/3d/README.md`.
  - USB-C uses the LCSC catalogue model shared with the battery board.
  - KiCad 10 has no models for the TS-1187A buttons or the MSK12C02 power switch. They use simplified envelopes built from the footprint and datasheet dimensions, with their build123d sources alongside.

## Cost

About **$4.63 (₹444) per board at 1000** boards:

| At 1000 boards | Per board |
|---|---:|
| Parts | $4.01 |
| 2-layer fabrication, 47 × 76 mm | $0.13 (4-layer, 80 mm was $0.30) |
| JLC assembly | $0.49 |

Five prototypes cost about $31 each, mostly JLC's per-order assembly setup; the bare 2-layer boards are about $2 for five. Details, assumptions and exclusions are in [review/COST.md](review/COST.md). Only the SCD41 (U8) and the J6/J8 headers are unfitted; the CO₂ supply (LDO U7 with C15, C16 and C42, about $0.24) is assembled so the sensor can be soldered in later on its own. The same design with its original parts was about $10.7 (₹1030) at 1000.

## E-paper option (J6, unfitted)

The stationary version can use an e-paper display instead of the TFT. The panel from the Rev A brief, Good Display GDEY037T03, is a bare panel: it needs a boost circuit (about ±15 V gate and source rails) on whatever board its 24-pin flex plugs into. Rev A put that circuit on this board as an unfitted option: 22 parts plus the FPC connector. Rev B leaves the boost circuit to an external adapter instead:

- **Adapter.** Good Display's DESPI-C02 takes the panel's 24-pin flex and makes the rails. The same adapter fits most of Good Display's 24-pin SPI panels, so the main board isn't tied to one panel. A module with its own driver board (for example Waveshare's) also works.
- **J6.** A 1 × 8, 2.54 mm SMD pin header on the back at the top-left edge (pads staggered at x = 3.35 and 6.66 mm, y = 1.5–19.3 mm). Like J8, it is unfitted (DNP) by default and is left out of the JLC BOM and placement files; solder it by hand for an e-paper build. It sits near the board edge, clear of J5, so there's room for the iron. It's surface-mount so no through-hole pads sit under the TFT in the default build. Pin 1 is at the top; the pin names are on the back silkscreen, on the side toward J5.

| J6 pin | DESPI-C02 pin | Signal | ESP32 |
|---:|---|---|---|
| 1 | BUSY | EPD_BUSY | GPIO20 |
| 2 | RES | DISP_RST | GPIO7 |
| 3 | D/C | DISP_DC | GPIO10 |
| 4 | CS | DISP_CS | GPIO4 |
| 5 | SCK | DISP_SCK | GPIO5 |
| 6 | SDI | DISP_MOSI | GPIO6 |
| 7 | GND | GND | |
| 8 | 3.3V | +3V2 (3.19 V) | |

A straight 8-way female-to-female cable maps J6 pin n to DESPI-C02 pin n. Waveshare modules use the same signals in reverse order (VCC, GND, DIN, CLK, CS, DC, RST, BUSY).

The display SPI, CS, DC and reset are shared with the TFT, so **fit one display only**. The adapter's supply comes from the +3V2 rail; e-paper refresh current is small. Firmware still has to supply a driver for the chosen panel: ESPHome has no working UC8253 (GDEY037T03) driver yet (see the Rev A brief), so either pick a panel ESPHome supports or bench-test a custom component.

## Interface to the battery board

- **USB-C J1 is the only power and data input.** It is the same SHOU HAN TYPE-C 16P L6.5 (LCSC C49287211) as the battery board's J1 and J7, using that board's footprint (checked against the maker's drawing) and 3D model. It is on the back, at x = 26.7 mm on the bottom edge (y = 76), with its mouth flush with the edge. That is about 11 mm nearer the centre than in Rev A. Plug it into the battery board's USB-C output J7, which carries 5 V plus USB data passed through from the battery board's input port. It can also plug straight into a computer or adapter.
- **J2: straight 2.54 mm Dupont header for battery %** (hanxia HX PZ2.54-1x2P ZZ, LCSC C32713268), back side, bottom-right, pin 1 at (33.85, 72.1) mm. The pins stand up from the back, toward the battery board; nothing overhangs the edge. Pin 1 = GND, pin 2 = BAT_PWM, the same order as battery J9, so a straight female-female jumper works. R33 (10 kΩ) pulls BAT_PWM up to +3V2; R34 (1 kΩ) feeds GPIO21. Encoding and receiver: `../firmware/telemetry/README.md`.
- **J8: straight Dupont header for external 5 V, unpopulated** (same part), next to J2 (pin 1 at x = 39.95 mm). Pin 1 = GND, pin 2 = 5 V in. D2 (B5819W Schottky, fitted) feeds +5V_SYS, the same point as USB VBUS. The switch and regulators work as normal, and the diode stops the board back-feeding the external supply. A supply above USB VBUS + 0.3 V can back-feed a connected USB host, so don't plug USB into a computer while an external 5 V is attached.
- Removed with the 10-way JST GH link:
  - the TS3USB30E USB data mux;
  - the TPS2116 power mux;
  - their FETs and resistors;
  - C4, C5, C6 and R24.

  No I2C runs to the battery board any more.

## Cost-down changes (same functions)

| Part | Rev A | Rev B |
|---|---|---|
| U5, U6 bucks | TPS62160 (MSOP-8) | Silergy SY8089A1AAC (SOT-23-5). The datasheet's optional feed-forward caps are omitted. |
| Buttons | MCP23008 I2C expander + C&K KMR2 | Straight to GPIOs; XKB TS-1187A 5.1 mm switches. U9, C17, R23 and R25 removed. |
| Backlight | STCS05A current sink (not stocked at JLC) | AO3400A low-side switch Q1 with R28 = 33 Ω 1206 (~55 mA at Vf 3.1 V). Still PWM-dimmable on GPIO3; the current is set by the resistor, not regulated. |
| Power switch | C&K JS102011SAQN | Shou Han MSK12C02; its actuator sticks out about 1.1 mm past the right edge. |
| USB-C | GCT USB4105 | SHOU HAN TYPE-C 16P L6.5, the battery board's part ($0.047 at 1000, against $0.103 for the HRO TYPE-C-31-M-12 it replaced) |
| Sensor connectors J3, J4 | JST GH | XYECO GH-compatible clones, same footprint |
| ESD, MCU | ST USBLC6-2SC6, ESP32-C3-MINI-1-H4 | Tech Public USBLC6-2SC6, ESP32-C3-MINI-1-H4X (same footprint) |

Every fitted part has an LCSC code in the schematic. `review/jlc-bom.csv` and `review/jlc-cpl.csv` are ready for JLCPCB assembly. The board is double-sided: the three buttons are on the front and everything else is on the back.

The TFT connector (TE 1-84953-0, $0.44) stays: no cheap top-contact 1.0 mm 10-pin FPC connector is stocked, and the display needs top contact.

## Firmware pin map

| ESP32 GPIO | Function |
|---|---|
| 10 | Display DC |
| 4 | Display CS |
| 5 | Display SCK |
| 6 | Display MOSI |
| 7 | Display RST |
| 8 | LEFT button, active low, R3 pull-up |
| 9 | OK button, active low, R2 pull-up. Hold OK while resetting to enter the ROM bootloader. |
| 2 | RIGHT button, active low, R4 pull-up |
| 21 | BAT_PWM input through R34. Use native USB for logs; do not enable UART TX on GPIO21. |
| 3 | Backlight PWM, now driving a MOSFET gate (R27 pull-down) |

GPIO2, 8 and 9 are boot-strap pins. Don't hold LEFT or RIGHT while resetting; OK held at reset is the intended download mode. The buttons need a pull-up at reset, which R2–R4 provide; there's no I2C expander any more.

The 2-layer layout changed the display pins so they leave the module in the TFT connector's order (DC, CS, SCK, MOSI, RST); this lets the bus run without crossings:

| | Rev A and 4-layer Rev B | 2-layer Rev B |
|---|---|---|
| DC | GPIO5 | GPIO10 |
| CS | GPIO10 | GPIO4 |
| SCK | GPIO4 | GPIO5 |

MOSI (GPIO6) and RST (GPIO7) are unchanged. The display SPI goes through the GPIO matrix either way. All other GPIOs are as in Rev A.

## Layout

Two layers. Nearly every part is on the back, so the back carries most signals, and the front carries ground plus the fixed routes below.

- **Ground.**
  - Both layers are poured with GND and stitched with 228 vias:
    - one beside every ground pad, placed before routing so the router must leave room for it;
    - a 2 mm edge fence;
    - a 3 mm field grid;
    - repair vias for any pocket.
  - All ground copper is one connected area except the CO₂ island, which joins through the bridge (see below).
  - The front pour covers about 76% of the board and the back about 64%.
- **Ground neck.** The CO₂ island's slots cut the right half of the board between y = 21 and 35 mm, so every return current between the top and bottom halves passes through the neck on the left. The front copper at x = 8.5–16 mm, y = 23.3–35.5 mm is kept free of signal tracks; vias are allowed. That keeps a continuous 7.5 mm ground bridge there.
- **Fixed routes** (drawn before autorouting, in `main_revb_2layer.py`):
  - **Display SPI.** DC, CS, SCK, MOSI and RST run as a 5-lane front bus. It starts with vias above the module's top pins, runs up the left edge and along y = 21–23 mm, then drops through vias beside J5's pads.
  - **Backlight PWM.** It takes the outermost left-edge lane.
  - **CO₂ island.** The island's copper enters through its 2.5 mm bottom-right tab (x = 41.5–44 mm, y = 34–35 mm); the left tab is mechanical only, with no copper. U8 (SCD41) is turned so its SDA, SCL, VDD and GND pins face the tab. SDA and GND cross on the back, SCL and +3V3_CO2 on the front, and they run down to U7 (the CO₂ LDO, beside J3) and the I²C bus. The widened strip beside the island (x = 44–45.5 mm) has no copper at all, so the island stays thermally isolated. Tracks keep 0.35 mm from all slot edges.
  - **Buttons.**
    - GPIO8 (LEFT) runs straight down the front.
    - GPIO9 (OK) goes past the module corner on the back, then down the front.
    - GPIO2 (RIGHT) leaves pin 5 on the back, up a via in the lane beside the module's centre ground pads, then along the front between the button pad rows.
  - **Battery PWM (GPIO21).** It crosses the bottom band on the front at y = 65.45 mm.
  - **E-paper BUSY.** It runs up the front from the module to TP5; the router takes it on to J6.
  - **USB.** The module-side pair threads past the pin-30/31 vias. D1's ground goes through a via under its body to the USB-C shield.
  - **Load switch U4.** CT, ON and QOD go directly to C8, R15 and R16.
- **Placement changes for two layers.**
  - U4 (load switch) took the CO₂ LDO U7's place and is turned 180°, so its control pins face their parts. U7 moved beside J3's 5 V pin, just below the island.
  - R7/R8 swapped, so the USB pair keeps the same order from the module through the resistors to D1.
  - R27, the backlight gate pull-down, sits beside Q1 between its gate and source pins (it was at the end of the left-edge backlight lane, where J6 now is).
  - C16 (the SCD41's 10 µF supply cap, assembled) is off the island, below U7's output (x = 25 mm, y = 42 mm), about 7 mm from the sensor body and across the slot. Hot air used to fit the SCD41 later won't lift it. It also acts as U7's bulk output cap. The island itself now carries only the sensor.
  - TP2/TP3 moved to the left edge (the touch-up moves TP3 beside R3 only if the router can't reach it there); C7, R2 and R3 moved up 1.5–3 mm to open a fan-out band above the module's top pins.
- **Routing and power.**
  - Freerouting routes the rest, with the back preferred. An A* finisher (`astar_finish.py`) closes what the router leaves, moving other tracks only when everything it moves reconnects.
  - Power nets are 0.6 mm except a few short 0.4–0.5 mm squeezes (about 6.5 mm of +3V2, 5 mm of +5V_SYS and 3 mm of +5V_SW). +3V3_CO2 is 0.25 mm through the island tab; the SCD41's peak draw is under 0.2 A.
- **Bucks.** Each SY8089's input cap, IC and inductor sit together on the back. Their grounds join the back pour, with vias to the front plane beside each ground pad.

## Checks (review/)

- **Results:** ERC 0. DRC with schematic parity: 0 errors, 0 warnings, 0 unconnected, 0 parity issues.
- **Exports:** `AQI_Main.pdf`, `netlist.xml`, `engineering-bom.csv`, `jlc-bom.csv`, `jlc-cpl.csv`, `COST.md`, `price-snapshot-2026-09-27.json`, `drc.json`, `erc.json`, layer SVGs and renders.
- **3D renders:** `main-top.png`, `main-bottom.png` and the two angled views. They include the display panel and its flex.
- `rev-a-baseline/` holds the untouched Rev A board; `rev-b-4layer-80mm/` holds the 4-layer, 80 mm Rev B that the 2-layer layout starts from.
- `routing/` holds the Freerouting input and output (`AQI_Main.dsn`, `.ses`, logs) and the list of fixed routes.

## Regenerating

Needs KiCad 10, a Java 25+ runtime (Homebrew `openjdk`) and Freerouting 2.4.1 (`~/Applications/freerouting/freerouting-2.4.1.jar`, or set `FREEROUTING`). Run from `../scripts`:

1. `main_revb_design.py` rebuilds `design.json` and the schematic.
2. Export `review/netlist.xml` (kicad-cli `sch export netlist --format kicadxml`).
3. `main_revb_2layer.sh` starts from `review/rev-b-4layer-80mm/` and runs each stage in turn:
   1. **Placement:** strips the copper, cuts the outline, moves parts, lays the fixed routes and ground fan-out, and writes the DSN.
   2. **Routing:** Freerouting, then the A* finisher.
   3. **Ground:** stitching and island repair.
   4. **Touch-up:** `main_revb_2layer_touchup.py`.
   5. **Sync:** writes positions back to `design.json`.
   6. **DRC.**
4. `main_revb_cost.py` recomputes `review/COST.md`. It picks up the layer count and board size from the board.

Freerouting's result depends on its input, so a rerun after any change gives a different board, and the finisher may need a hand. The 4-layer flow (`main_revb_layout.py`) still rebuilds the 80 mm board.

Hand edits made in KiCad are not captured by the scripts. Once you edit the `.kicad_pcb` by hand, treat it as the source of truth.

## Open items before fabrication

1. **Antenna.** The module sits on the back, facing the battery board. Keep the 18650 cell, holder terminals and cables away from the bottom-left corner.
   - With the shorter board, the antenna keepout ends about 1.3 mm from the LEFT button's pads (it was 5 mm).
   - USB-C is about 6 mm from the keepout.
   - Measure Wi-Fi/BLE range in the enclosure, with the USB cable plugged in.
   - On two layers the module also has no inner ground plane under it; its ground pads stitch to the front pour instead.
2. **Backlight current.** R28 = 33 Ω assumes a ~3.1 V LED forward voltage at ~55 mA. Check brightness and current on the actual panel and adjust R28.
3. **Enclosure.** Allow for:
   - the 47 × 76 mm board, with the 1 mm copper-free clamping lips on both long sides;
   - the J2/J8 straight headers: about 8.5 mm tall on the back, plus the Dupont housings (your CAD test fit shows room);
   - J3/J4 mouths at x = 37.5 mm, with the GH plug and cable bend in the 8 mm to the right edge;
   - the SW4 actuator about 1.1 mm past the right edge;
   - USB-C on the back at x = 26.7 mm;
   - the button row at x = 9, 22, 35 mm, y = 66.25 mm, with caps or plungers to reach past the display thickness.
4. **2-layer review.** Before ordering, look over the routing in KiCad, especially:
   - the CO₂ island's tab feed;
   - the U4 corner by the slot;
   - the left-edge display bus.
5. **Firmware.** Apply the pin map above:
   - buttons on GPIO8/9/2 instead of the MCP23008;
   - battery % from BAT_PWM;
   - the display on DC = GPIO10, CS = GPIO4, SCK = GPIO5;
   - for the e-paper build, BUSY on GPIO20 and a driver for the chosen panel.
6. **USB-C supply and fit.** LCSC had only 2,553 of C49287211 in stock (2026-09-27). The battery board uses two per set, so 1000 sets need 3000. Reserve stock or approve the HRO TYPE-C-31-M-12 as the alternate, which needs a footprint and breakout change. SHOU HAN's drawing is for 0.8 mm boards, so check shell-leg soldering and retention on this 1.6 mm board. The battery board has the same open check. In JLC's placement preview, confirm J1's rotation: its footprint comes from the EasyEDA catalogue.
7. **Pricing.** Get a real JLCPCB quote. The cost uses catalogue tiers and published assembly rates, not a quotation.
8. Rev A items 1 and 3–6 in `../../rev-a/README.md` still apply: enclosure, USB current, sensor/CO₂ and display validation.
