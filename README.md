# Portable AQI Recorder

A compact, battery-friendly Air Quality Index monitor built with an **ESP32-C3 Super Mini** and **Sensirion SEN50** particulate matter sensor. View real-time PM1.0, PM2.5, PM4.0, and PM10.0 readings on your phone over **Bluetooth Low Energy** using the Sensirion MyAmbience app.

## Features

- **Real-time PM monitoring** — PM1.0, PM2.5, PM4.0, PM10.0 (µg/m³)
- **US EPA AQI calculation** — computed from PM2.5 & PM10, printed to serial
- **BLE streaming** — connect with Sensirion MyAmbience app on iOS/Android
- **Data logging** — download measurement history from the app
- **Tiny form factor** — ESP32-C3 Super Mini is just 22×18 mm

---

## Hardware

| Component | Description |
|---|---|
| **ESP32-C3 Super Mini** | Microcontroller with BLE & Wi-Fi |
| **Sensirion SEN50** | PM-only environmental sensor module |

### Wiring

| ESP32-C3 Super Mini | SEN50 (JST connector) |
|---|---|
| GPIO 8 (SDA) | Pin 4 — SDA |
| GPIO 9 (SCL) | Pin 3 — SCL |
| GND | Pin 2 — GND |
| 5V | Pin 1 — VDD |

> [!IMPORTANT]
> The SEN50 **requires 5V** for its internal fan. Power it from a 5V source (e.g. USB VBUS), not the ESP32's 3.3V output. The I2C lines are 3.3V tolerant — no level shifter needed.

#### SEN50 JST Pinout (left to right, notch facing up)

```
Pin 1 — VDD  (5V)
Pin 2 — GND
Pin 3 — SCL
Pin 4 — SDA
Pin 5 — SEL (leave unconnected or tie to GND for I2C)
Pin 6 — NC
```

---

## Software Setup

### Prerequisites

1. **PlatformIO** — Install the [PlatformIO IDE extension](https://platformio.org/install/ide?install=vscode) in VS Code, or install the [PlatformIO CLI](https://docs.platformio.org/en/latest/core/installation.html).

2. **Sensirion MyAmbience App** — Install on your phone:
   - [iOS (App Store)](https://apps.apple.com/app/sensirion-myambience/id1529131572)
   - [Android (Play Store)](https://play.google.com/store/apps/details?id=com.sensirion.myam)

### Build & Upload

1. **Clone the repository**
   ```bash
   git clone https://github.com/devalopr/Portable-AQI-recorder-.git
   cd Portable-AQI-recorder-V1
   ```

2. **Build the firmware**
   ```bash
   pio run
   ```
   > If `pio` isn't in your PATH, use the full path:
   > `C:\Users\<YOU>\.platformio\penv\Scripts\pio.exe run`

3. **Upload to ESP32-C3**
   
   Connect the ESP32-C3 Super Mini via USB-C, then:
   ```bash
   pio run -t upload
   ```

4. **Monitor serial output** (optional)
   ```bash
   pio device monitor
   ```
   You'll see PM values and calculated AQI:
   ```
   PM1.0: 5.20   PM2.5: 8.10   PM4.0: 9.30   PM10.0: 10.50   | AQI(PM2.5): 34  AQI(PM10): 10  => AQI: 34 [Good]
   ```

---

## Connecting to the App

1. Open the **Sensirion MyAmbience** app on your phone.
2. Make sure Bluetooth is enabled.
3. The device should appear automatically — look for a device ID matching the one shown in serial output.
4. Tap to connect and view real-time PM data.
5. You can also download historical data from the device's log.

---

## AQI Reference

The firmware calculates the **US EPA Air Quality Index** from PM2.5 and PM10. The overall AQI is the higher of the two sub-indices.

| AQI Range | Category | Color |
|---|---|---|
| 0 – 50 | Good | 🟢 Green |
| 51 – 100 | Moderate | 🟡 Yellow |
| 101 – 150 | Unhealthy for Sensitive Groups | 🟠 Orange |
| 151 – 200 | Unhealthy | 🔴 Red |
| 201 – 300 | Very Unhealthy | 🟣 Purple |
| 301 – 500 | Hazardous | 🟤 Maroon |

> **Note:** The Sensirion MyAmbience app displays raw PM values (µg/m³). AQI is printed to the serial monitor only, as the BLE protocol does not have a custom AQI signal type.

---

## Project Structure

```
Portable-AQI-recorder-/
├── src/
│   └── main.cpp          # Main firmware (sensor + BLE + AQI)
├── platformio.ini         # PlatformIO configuration
└── README.md              # This file
```

## Dependencies

All dependencies are managed automatically by PlatformIO:

| Library | Version | Purpose |
|---|---|---|
| Sensirion I2C SEN5X | ^0.3.0 | I2C driver for SEN50 sensor |
| Sensirion Gadget BLE Arduino Lib | ^1.2.0 | BLE data provider for MyAmbience app |
| Sensirion UPT Core | ^0.3.0 | BLE protocol definitions |
| NimBLE-Arduino | ^1.4.1 | Lightweight BLE stack for ESP32 |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `pio` not found | Use full path `~/.platformio/penv/Scripts/pio.exe` or add it to PATH |
| Serial shows no output | Wait 2–3 seconds after reset; check baud rate is **115200** |
| All PM values are 0.00 | SEN50 fan needs ~10 seconds warm-up after startup |
| BLE device not visible | Re-check wiring; ensure SEN50 has 5V power |
| Upload fails | Hold BOOT button on ESP32-C3, click upload, release BOOT after "Connecting..." |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
