# Integrated power shortlist — 2026-09-11

Research only; no circuit or procurement metadata substitutions applied. Preserve cost-revision/BOM-HANDOFF.md and its baseline until a replacement circuit is qualified.

User decision: IP5306-I2C selected for the redesign. Retain approximate PWM battery reporting and 3.3 V/1 A output. Minimize total assembled cost while retaining the requested features. Selection does not mean the qualification gates below have passed or the schematic has been migrated. Existing CH32V003F4P6 (C5187096) costs USD0.1627 at the applicable 500+ tier for 1,000 boards, or INR15.62 at the planning exchange rate; programming and assembly are additional.

Required: 5 V/2 A output, separate 3.3 V/1 A buck rail, approximate battery percentage over open-drain PWM, three-position charge selection, two USB-C ports, GH power/data/telemetry, cell protection. The outputs share available converter power; this research does not establish simultaneous 10 W + 3.3 W capability.

## Catalogue snapshot

PCBParts LCSC-linked jlc_get_part results; 1,000 IC purchase, USD96 conversion to INR. Prices exclude passives, PCB and all manufacturing costs. Stock is a database snapshot, not reserved inventory.

| Exact part | LCSC | Applicable USD tier | INR/IC | Stock |
|---|---|---:|---:|---:|
| ETA9740E8A | C7465512 | 0.1531 (500+) | 14.70 | 2757 |
| IP5306-I2C | C488349 | 0.2108 (500+) | 20.24 | 4221 |
| IP5310 (standard, NOT verified I2C variant) | C191176 | 0.3139 (1000+) | 30.13 | 7261 |

## Evaluation

IP5306-I2C is the leading prototype candidate: combined charger/boost, register-controlled charging and always-on function. Keep the CH32 ADC-based estimate and PWM output; the PMIC does not provide numerical voltage/current measurements. I2C is internal only. Use a battery-derived MCU supply as recommended by its register application note, so configuration is possible independently of boost startup.

Qualification gates: source exact I2C variant; verify register settings and reset behavior against original-language manufacturer documentation; implement conservative hardware input limiting before firmware config; verify battery-current control (0x23 loop selection versus 0x24 VIN-labelled current setting); test low-load persistence, USB unplug transitions, short circuits, thermal performance and 2 A at low battery. Do not promise exact 0.5/1/1.5 A from unverified register arithmetic. The documented current grid is 50 mA + 100 mA steps, and termination minimum is 200 mA. These matter at the lowest charge rate. USB-C CC handling and input/output isolation are still required; this is not a complete two-port USB-C controller.

ETA9740E8A is the lower-priced hardware-selector alternative: manufacturer specifies 3 A charging, 5 V/2.4 A boost and resistor ISET. Public table only specifies 56k/3 A and 91k/2 A; it does not establish the required lower-current ladder. Shared bidirectional OUT node needs external input isolation. Public documentation is insufficient to approve low-load behavior, exact 0.5/1/1.5 A settings or two-port operation. Do not extrapolate resistor values into the production schematic.

IP5310 integrates Type-C, NTC, power path and nominal 3.1 A boost, offering more power headroom. However, its Type-C block serves one DRP port, not two independently controlled ports. Its manufacturer document explicitly requests IP5310_I2C for I2C use; C191176 pricing must not be assigned to that unverified variant. Standard device auto-sleeps below approximately 45 mA after 32 s. Register availability, variant sourcing, charge settings and CV tolerance remain gates.

Retain a switching buck from the 5 V internal rail to 3.3 V; existing SY8089A1AAC remains a candidate. A linear regulator would dissipate (5-3.3)*1 = 1.7 W. A 90%-efficient buck supplying 3.3 V/1 A draws approximately 0.733 A from 5 V, leaving about 1.27 A of a 2 A shared budget for external 5 V loads. These are planning calculations, not measured efficiency or qualified output ratings.

## Manufacturer documents and catalogue references

- ETA9740 V1.1: https://www.eta-semi.com/wp-content/uploads/2022/03/ETA9740_V1.1.pdf
- Injoinic IP5306 register file V1.21, translated manufacturer document mirror: https://done.land/assets/files/ip5306_i2c_registers.pdf
- Injoinic IP5310 V1.37, manufacturer document mirror: https://wiki.geekworm.com/images/c/ce/IP5310-datasheet-en.pdf
- https://www.lcsc.com/product-detail/battery-management_injoinic-ip5306-i2c_C488349.html
- https://www.lcsc.com/product-detail/battery-management_etasolution-eta9740e8a_C7465512.html
- https://www.lcsc.com/product-detail/battery-management_injoinic-ip5310_C191176.html

No full revised board cost is established by these IC prices.
