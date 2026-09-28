# Battery PWM interface, revision 1

Current battery schematic: `integrated-power/AQI_IP5310_Power.kicad_sch` in the [18650-USB-C-UPS](https://github.com/devalopr/18650-USB-C-UPS) repo, which also holds the CH32 transmitter firmware and a copy of this folder. The older `cost-revision` is preserved for history. Portable ADC/estimator and charging integration now lives in that repo's `firmware/control`; target hardware binding remains unfinished.
Main schematic: `../../main-pwm/AQI_Main.kicad_sch`.
These are circuit revisions; the existing routed boards do not implement this interface yet. Do not manufacture from old STEP/ZIP/Gerber files as if they did.

## Electrical connection

Current integrated-power revision: J9 pin 2 and TP8 carry open-drain BAT_PWM; J9 pin 1 is GND. The receiver supplies its 10k pull-up to 3.3V. J3/GH and its USB branch have been removed. Older main-pwm hardware still brings this signal to GH pin 7 and needs an adapter or connector revision. Older I2C battery-interface firmware is incompatible.

Q5 is a 2N7002 open-drain output, source to GND, gate driven by CH32V003 PC1/package pin11. R49 (100k) holds the gate off during reset. Connect a **10k pullup to the host's 3.3V or 5V logic supply**, and share ground. Do not pull up to battery voltage. No pullup is fitted on the battery board, avoiding back-power into an unpowered host. Intended for short internal/hobby wiring, not a long external cable or an ESD-qualified industrial port.

Main revision: R33 pulls BAT_PWM up to +3V2; R34 (1k) connects it to ESP32 GPIO21/package pin31. TP4 is now BAT_PWM_MCU. The resistor limits contention during ROM UART output at startup. Use native USB logging and configure GPIO21 as input; do not enable UART TX on it. Sensor I2C, native USB and e-paper BUSY/GPIO20 are unchanged. Main schematic ERC and all intended connected pins in the exported netlist have been checked.

## Encoding

100Hz nominal, 10ms frame. **HIGH duty** = 10% + 0.8 × percentage, so 0% battery is 1ms high, 50% is 5ms high, and 100% is 9ms high. The MOSFET inverts its gate signal; the CH32 driver accounts for that.

Decode `percent = (high_time / period - 0.1) / 0.8 * 100`. No transitions means unavailable, never 0% or 100%. Receiver accepts periods 9–11ms, tolerates 9–91% wire duty at the endpoints, requires three valid complete frames, and expires the last value after 100ms. This is an approximate voltage-based estimate, not a calibrated fuel gauge.

## Firmware

- `battery_pwm.h`: shared encoding/decoding, no framework dependency.
- `battery_pwm_ch32.c`: PC1 output using TIM2 update/compare interrupts, 1MHz timer count. Call `battery_pwm_init(actual_TIM2_clock_hz)` once, then `battery_pwm_submit(percent, valid)` at least once per second from the battery estimator. It releases the output after two seconds without an update. Use `valid=false` for unavailable/invalid measurements. Calls must originate in the main loop, not a higher-priority interrupt.
- WCH project interrupt wrapper:

```c
void TIM2_IRQHandler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void TIM2_IRQHandler(void) { battery_pwm_tim2_irq(); }
```

Use WCH's CH32V003 SDK, correct startup/linker script and RV32EC toolchain. TIM2 is reserved for telemetry. Do not block interrupts for long periods. Driver API/type syntax was checked against the official WCH SDK; it has **not** been linked into a CH32 image or flashed. The battery ADC estimator/RGB application integration remains pending; this module does not implement charging or the estimator itself.

- `BatteryPwmReader.h/.cpp`: ESP32 Arduino receiver using a GPIO edge interrupt, no busy-wait pulse reads.
- `receiver_example.cpp` and `platformio.ini`: standalone GPIO21/USB diagnostic example, successfully built for ESP32-C3 using Arduino-ESP32 2.0.14. This example is not the AQI application and should not replace it wholesale.

Build receiver: `pio run -d hardware/rev-b/firmware/telemetry` from repository root.
Run protocol test: `clang -Wall -Wextra -Werror hardware/rev-b/firmware/telemetry/test_protocol.c -o /tmp/aqi-pwm-test && /tmp/aqi-pwm-test`.

Hardware validation still required: waveform/polarity and startup on both boards, 3.3V/5V pullups, host unpowered behavior, estimator calibration, and worst-case ISR latency. No hardware test is claimed.

Sources: WCH official SDK https://github.com/openwch/ch32v003 ; ESP32-C3-MINI pinout https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.html .
