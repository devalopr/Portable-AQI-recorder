# Portable AQI Recorder — V3 (custom PCB)

A handheld air-quality recorder on a custom main board: an ESP32-C3-MINI-1 module reads a Sensirion SEN5x or SEN6x particulate sensor and an optional SCD4x CO₂ sensor (SCD40, SCD41 or SCD43), shows readings on a 2.4" ST7789 TFT with three buttons, and has Wi-Fi and BLE on the module.

This branch holds the **V3 main PCB only**. Everything else lives elsewhere:

| What | Where |
|---|---|
| ESP32-C3 Super Mini build without a PCB: firmware, Web Bluetooth app, wiring | [V2 branch](https://github.com/devalopr/Portable-AQI-recorder/tree/V2) |
| 18650 battery board (IP5310, USB-C in/out, battery % over PWM) | Separate product: [18650-USB-C-UPS](https://github.com/devalopr/18650-USB-C-UPS) (private) |
| Rev A boards and earlier design history | Git history of this branch (commit `34dd5cf`) |

## Main board (Rev B)

**[hardware/rev-b/main](hardware/rev-b/main/README.md)** — KiCad 10 project, 47 × 76 mm, two layers, fully routed. Start with its README: layout, pin map, connectors, cost, checks and open items before fabrication.

- **Display:** 2.4" 240 × 320 ST7789 TFT on the front, with the three buttons below it. An e-paper display can be fitted instead through an external adapter on J6.
- **Sensors:** SEN5x and SEN6x connectors (fit one PM module) and a CO₂ island for an optional SCD40, SCD41 or SCD43, soldered by hand later. Everything else on the board comes assembled; only the CO₂ sensor and the J6/J8 headers are left unfitted.
- **Power and data:** USB-C J1 is the only input. It takes 5 V and USB data from the battery board's USB-C output, or straight from a charger or computer. Battery % arrives as PWM on J2.
- **Cost:** about $4.63 per board at 1000 (parts, 2-layer fabrication and JLC assembly); see [review/COST.md](hardware/rev-b/main/review/COST.md).

## Repository layout

| Path | Contents |
|---|---|
| [firmware](firmware/README.md) | Main board firmware (PlatformIO). |
| [hardware/rev-b/main](hardware/rev-b/main/README.md) | Schematic, PCB, libraries and 3D models; `review/` has the BOM, placement file, PDF, renders, DRC/ERC reports and routing files. |
| [hardware/rev-b/scripts](hardware/rev-b/scripts) | Python/shell pipeline that generates the schematic and places, routes and checks the board (see "Regenerating" in the main README). |
| [hardware/rev-b/firmware/telemetry](hardware/rev-b/firmware/telemetry/README.md) | ESP32 receiver for the battery board's battery-% PWM signal. |
| [hardware/rev-b/references](hardware/rev-b/references) | Datasheets for parts on this board. |
| [hardware/design-brief.md](hardware/design-brief.md) | The original product brief the boards were designed from. |

## Firmware

**[firmware/](firmware/README.md)** — PlatformIO/Arduino firmware for this board, ported from the V2 firmware: auto-detects SEN5x or SEN6x and any SCD4x, shows AQI and the other readings on the TFT, records to RAM, streams over BLE (compatible with the V2 web app) and shows the battery % from the battery board. It builds but hasn't run on a built board yet.

The board is programmed and logs over its USB-C port (the ESP32-C3's native USB): switch the board on and run `pio run -t upload` in `firmware/`. If it stops appearing, hold OK while switching it on to force the bootloader.
