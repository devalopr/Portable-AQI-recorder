# Rev A firmware integration

The existing src/ firmware belongs to the wired prototype and has not been silently changed. Use this allocation when adding a Rev A board target.

| ESP32 GPIO | Function |
|---|---|
| 0 | I2C SDA |
| 1 | I2C SCL |
| 3 | Backlight PWM |
| 4 | Display SPI SCK |
| 5 | Display DC |
| 6 | Display SPI MOSI |
| 7 | Display RESET |
| 10 | Display CS |
| 18 | Native USB D− |
| 19 | Native USB D+ |
| 20 | E-paper BUSY / UART RX test pad |
| 21 | UART TX test pad |
| 2, 8, 9 | Boot straps; retain pullups, GPIO9 is the recovery boot pad |

Main MCP23008: address 0x20. GP0 = left, GP1 = OK, GP2 = right, active low; use input mode and the fitted external pullups. Battery MCP23008: address 0x21. GP0 = BQ24074 EN1, GP1 = EN2; GP2 = charge status, GP3 = input-power-good status. Status pins are active low. Leave unused expander ports as inputs.

BQ24074 EN2/EN1 states: 00 = 100 mA input limit, 01 = 500 mA, 10 = external ILIM resistor, 11 = suspend. Initialize output latches before changing expander direction. Do not select a higher input current without qualifying the source. The 1.50 kΩ ILIM resistor sets approximately 1.07 A typical when that mode is permitted, with tolerance; it is not a USB entitlement.

MAX17048 address 0x36: SOC is at register 0x04 (MSB + LSB/256 percent). Read VCELL at 0x02 as an unsigned 16-bit word, MSB first, and multiply by 78.125 µV to obtain volts; preserve all bits. Read both bytes in one transaction. These register units are specified in Table 2 of the [MAX17048 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max17048-max17049.pdf). Implement temperature compensation and low-battery load shutdown; the protector is the final cutoff, not the normal discharge endpoint. SOC is an estimate and needs validation with the chosen cell.

For stationary ESPHome operation, the battery assembly is absent. Use the main USB-C and a suitable adapter. The MCU, GPIO expander and sensor buses are compatible with ESPHome. The exact GDEY037T03/UC8253 display integration still requires a verified component/driver; no working ESPHome display configuration or compiled firmware is claimed here. GxEPD2's exact panel implementation is a reference for that work.
