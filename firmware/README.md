# Main board firmware (V3)

PlatformIO / Arduino firmware for the main board Rev B ([hardware/rev-b/main](../hardware/rev-b/main/README.md)). It is a port of the V2 Super Mini firmware to this board's pins, sensors and three buttons. It builds, but **it has not run on a built board yet**; see "Not yet verified" below.

## Build and flash

Needs [PlatformIO](https://platformio.org/) (the VS Code extension or `pip install platformio`). From this folder:

```bash
pio run -t upload
```

```bash
pio device monitor
```

## Programming over USB

Yes: the board is programmed and logs through its USB-C port J1, with no adapter or extra buttons.

- J1's data pair goes to the ESP32-C3's built-in USB Serial/JTAG port (GPIO18/19) through R7/R8 and the D1 ESD protector. A computer sees a USB serial port; esptool (used by `pio run -t upload`) resets the chip into the bootloader and back over USB by itself.
- **The power switch must be on.** SW4 switches the regulators that power the ESP32, so with the switch off the board is invisible to the computer even though USB is plugged in.
- It also works through the battery board: plug the computer into the battery board's input, and the battery board passes USB data to its output, which feeds J1. That pass-through is Full Speed only and untested, so use a direct cable to J1 if it misbehaves.
- **If the port disappears** (e.g. firmware that crashes at boot or reuses GPIO18/19): hold **OK** while switching the power on. GPIO9 low at power-up starts the ROM bootloader, which always comes up on USB. Flash, then switch off and on. TP3 (GPIO9) and TP2 (EN, reset) are also on the back for a test fixture.
- Serial logs use native USB CDC (`ARDUINO_USB_CDC_ON_BOOT`). Don't enable UART0: its TX pin, GPIO21, is the battery-% input.

## What it does

| Feature | Details |
|---|---|
| PM sensor | Auto-detected at boot: SEN50/54/55 on J3 (I²C 0x69) or SEN63C/65/66/68 on J4 (I²C 0x6B). Fit one. |
| CO₂ | Any SCD4x on the CO₂ island (I²C 0x62): SCD40, SCD41 or SCD43, identified at boot and logged. Otherwise the SEN63C/SEN66's built-in CO₂. The SCD4x wins if both are present. |
| AQI | US EPA AQI from PM2.5 and PM10, unchanged from V2 (above 500 continues the 301–500 slope). |
| Display | ST7789 240 × 320 on J5; home screen, full-screen charts. Backlight PWM on GPIO3 (Q1). |
| Battery | Battery % from the battery board's PWM on J2 → GPIO21 (`hardware/rev-b/firmware/telemetry`); shows `--` without it. |
| Recording | RAM ring buffer, 2700 samples (45 min at 1 Hz), charted on the device. |
| BLE | Same service and packet as V2, so the [V2 web app](https://github.com/devalopr/Portable-AQI-recorder/tree/V2/web) works. Two fields are appended (CO₂ ppm u16, battery % u8); the V2 app ignores them and shows SEN6x sensors as "Unknown". |

### Buttons

| Button | Home screen | Chart |
|---|---|---|
| LEFT / RIGHT | Move the selection | Previous / next chart |
| OK | Open the chart for the selection; on the gear, cycle brightness (100/70/40/15 %, remembered) | Back to home |
| Hold OK (0.8 s) | Start / stop recording | Start / stop recording |

Don't hold LEFT or RIGHT while switching on (they are boot-strap pins).

## Configuration

`platformio.ini` holds the display pins and `DISPLAY_ROTATION` (2 = image turned 180° because the display flex exits at the top). If the image comes out upside down on the real panel, change it to 0.

## Not yet verified on hardware

- Display orientation, colour order and inversion (`DISPLAY_ROTATION`, `TFT_RGB_ORDER`, `TFT_INVERSION_OFF`).
- Backlight brightness steps against R28.
- SEN6x start-up timing and each SEN6x variant's detection (only the drivers' interfaces were checked).
- The SCD4x on the island, and its temperature offset with the board running.
- Battery % from a real battery board.
- The e-paper option (J6) has no driver in this firmware; it builds for the TFT only.
