# AQI main-board PWM circuit revision

**Superseded by [../main](../main/README.md)**: the battery board no longer has a GH connector, so the main board now takes USB-C power/data and a 2-pin Dupont PWM header.

Open `AQI_Main.kicad_pro`. This schematic adapts the main board to the new standalone battery PWM output; it is separate from the earlier routed Rev A board.

- GH J2 pin7: BAT_PWM; pin8: NC.
- R33: 10k pullup to the main core rail (+3V2).
- R34: 1k series resistor into GPIO21, formerly UART TX.
- TP4 follows GPIO21 and is labelled BAT_PWM_MCU.
- USB programming/logging and sensor/display interfaces remain available.

ERC zero; all intended connected pins match the exported netlist. No PCB has been routed for this circuit revision. The original Rev A PCB must not be treated as matching this schematic.

Firmware, protocol and hardware-validation details: `../firmware/telemetry/README.md`.
