# Pre-layout circuit and cost gate

Updated 2026-09-12. User explicitly requires circuit/schematic review and board costing before placement or routing. Neither placement nor routing is authorized to proceed past this gate yet. This is an engineering status record, not a validated circuit release.

## Latest requirement

Current authorized scope is two models only, each with ONE shared charger/boost stage:

| Model | Parallel cells | Total rated 5 V capacity | USB-C advertisement/output |
|---|---|---|---|
| One-cell | 1S1P | 2 A | 1.5 A |
| Two-cell | 1S2P | 3 A | 3 A |

Both keep 3.3 V / 1 A within the shared power budget, PWM battery reporting, a dim RGB indicator, adjustable charging, optional NTC, two USB-C ports and GH interconnect. Common components are preferred, with factory-set variant configuration. Four-cell/Pi-5/5-A variants are out of scope. The higher model targets Pi 3/4 with minimal peripherals. These are requirements, not validated measured ratings. The single-cell model may still deliver 2 A through its power pads within the common budget.

At 15 W / 90% efficiency / 3.0 V, pack current is 5.56 A, ideally 2.78 A per cell in 1S2P. Actual sharing depends on cell and contact resistance. Parallel holders require a reviewed reverse-insertion/equalization/protection arrangement. Charging the larger pack at unchanged current increases charging time. Voltage alone cannot identify how many parallel cells are fitted.

Official Raspberry Pi guidance: https://www.raspberrypi.com/documentation/computers/getting-started.html

IP5306-I2C was selected before the Pi requirement was clarified. Its available manufacturer documents specify approximately 2.1–2.4 A boosting, not a qualified 3 A output. It is unsuitable for guaranteeing this updated USB-C target. Do not continue its placement or describe it as Pi 4 qualified. A new integrated-power engineering schematic now exists in ../integrated-power. The preceding discrete circuit remains preserved in ../cost-revision. See the latest status below.

## Calculations

- 5 V * 3 A = 15 W external load.
- At 90% boost efficiency and a 3.0 V cell, battery current is 15/(0.90*3.0) = 5.56 A. At 85%, it is 5.88 A. These are design estimates, not measured efficiency.
- A total 50 milliohm resistance in the holder/protection path dissipates about 1.54 W at 5.56 A, before converter loss. Generic holder current capability/contact resistance must therefore be measured or specified; outer dimensions alone are insufficient.
- Boost converter loss at 15 W and 90% efficiency is 1.67 W. A compact two-layer layout must be thermally qualified at minimum cell voltage and enclosure temperature.
- A 3.3 V / 1 A buck at assumed 90% efficiency uses 3.67 W, or 0.733 A from 5 V. A 3 A internal 5 V budget therefore leaves about 2.27 A for external 5 V loads when 3.3 V supplies its full 1 A. Do not advertise simultaneous full rail maxima.
- With 5.0 V at the board and a 4.63 V undervoltage threshold, the simple total cable/connector resistance budget at 3 A is (5.0-4.63)/3 = 0.123 ohm. Ripple and transients consume additional margin. Reference: https://www.raspberrypi.com/documentation/computers/raspberry-pi.html
- USB Type-C current advertisement has default, 1.5 A and 3 A levels. USB-PD could negotiate other currents, but IP5306 does not itself implement PD. A 2 A boost cannot simply advertise 3 A. USB-C specification mirror: https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/USB-Type_2D00_C-Spec-R2.4-_2D00_-October-2024.pdf

## Candidate status

IP5310_I2C is now the leading common-stage candidate. Exact LCSC C20616661 was found using the live catalogue including out-of-stock parts. Its 1,000+ price is USD0.3304 (INR31.7184 at INR96/USD), with ZERO stock on 2026-09-12. This is distinct from standard IP5310 C191176. Replenishment price and lead time remain unconfirmed. No substitution has been applied.

The original-language manufacturer register manual V1.28 is saved as IP5310-registers-V1.28.pdf. It identifies:
- 0x00 bit2: 5 V always-on, but I2C can still shut down at light load.
- 0x02 bits7:5: 111 disables light-load shutdown; only these bits should be modified.
- 0x18 bits1:0: separate Type-C source/sink enables. Reset-state port behaviour still needs confirmation.
- 0x25 bit4 must clear before 0x23 bit5 can select the VIN charging control loop.
- 0x24: VIN-port current uses 50 mA plus weighted 100/200/400/800/1600 mA bits.
- 0x26: VBUS-port BAT-current uses DIFFERENT weights, 100/200/500/1200/2300 mA plus 50 mA. Never reuse IP5306 current encoding blindly.
- 0x21 minimum listed termination current is 300 mA, relevant to a nominal 500 mA charge setting.
- 0x74 provides coarse percentage bands; retain independent MCU voltage estimation for PWM as requested.

The single integrated CC controller still does not implement both independent USB-C ports. Current estimate conservatively retains input CC detection and an output CC/switch candidate. Whether input CC can be integrated economically depends on documented reset defaults, input isolation, charging path choice and current settings. Do not assume this cost saving before circuit review.

IP5328P C188809 and IP5328P-PPATH-100MA C605438 were both confirmed zero stock. SW6106 had no stocked search result. IP5356M_LBZ_CB C46550232 was stocked (3459) but costs USD0.5827 / INR55.94 at 1000+ and its exact control interface has not been qualified. These are fallbacks, not replacements.

## Cost status

The existing discrete baseline from cost-revision/BOM-HANDOFF.md remains INR261.21 for a priced subset plus holder, excluding unresolved parts and all manufacturing. It is not an acceptable final design cost.

Verified selected/common IC and connector figures at 1,000 boards, INR96/USD planning exchange rate:

| Item | INR each | Basis |
|---|---:|---|
| CH32V003F4P6 MCU | 15.62 | C5187096, USD0.1627, 500+ tier |
| SY8089A1AAC 3.3 V buck IC | 5.20 | C479074, USD0.0542, 1000-board handoff |
| SHOU HAN 16-pin input USB-C candidate | 4.86 | C2765186, USD0.0506 |
| SHOU HAN 6-pin output USB-C candidate | 2.27 | C456012, USD0.0236; port compatibility still under review |
| Genuine JST GH 10-pin | 18.74 | C2683602, USD0.1952 |
| Generic holder | 30.00 | User sourcing allowance, not a manufacturer quotation |

These six lines total approximately INR76.70 (rounded line values sum to INR76.69). They exclude the integrated power IC, USB control/switching still required, inductors, capacitors, resistors, RGB LED, charge selector, protection, PCB, assembly, programming and testing. This is a common-cost floor, NOT a completed revised BOM or a factory-cost prediction. A complete estimate must price every retained line, identify assumptions separately and obtain manufacturing charges; do not fill missing categories with undocumented quoted-looking numbers.

## Release gates

1. Select and source exact 3 A-capable integrated part with documented adjustable charging and stable light-load behavior.
2. Review full schematic against exact variant datasheets, including startup without firmware, low-cell recovery, source-current detection, input reverse-current blocking, port attachment and charger/load priority.
3. Prove the charge selector's actual battery-current settings. IP5306 register 0x24 is labelled VIN current even though 0x23 selects the loop; 450/950/1450 mA arithmetic alone does not establish battery current.
4. Review MCU supply/reference accuracy, I2C voltage levels, ADC and PWM paths, reset/fault handling and RGB/NTC population variants.
5. Complete ERC and intended-pin/net comparison plus visual schematic review. A clean ERC cannot establish analog performance.
6. Produce a full quantity-tier BOM with unresolved lines explicitly called out, plus PCB/assembly/programming/test quotation or clearly labelled estimate. Keep the INR200 ceiling visible.
7. Only then begin placement/routing. Prototype thermal, transient, charge, protection and Pi load testing is still required before a production performance claim.

## Current estimate and release decision

See common-stage-cost-estimate.md and its reproducible script ../scripts/prelayout_budget.py. The conservative IP5310_I2C candidate architecture estimates INR200–258 for one cell and INR234–298 for two cells including holder(s), with explicitly unquoted manufacturing/component allowances. These are NOT complete, qualified BOM quotations. The INR200 ceiling has not been achieved or established. Further part qualification and cost reduction are required before layout.

The integrated-power schematic is now generated: 0 ERC violations and 258 connected-pin checks passed, with 69 critical assertions. It remains an ENGINEERING DRAFT: protection, input startup/CC behavior, power passives, exact procurement and firmware are not finalized. See ../integrated-power/review/RELEASE-STATUS.md. Earlier KiCad files and other task's BOM handoff are preserved. No placement or routing started.

## 2026-09-12 schematic implementation update

User confirmed retaining IP5310_I2C. New project: ../integrated-power/AQI_IP5310_Power.kicad_pro. Its 77 fitted purchased placements include a new MCU-only ME6211 supply and BAT54C diode-OR to support startup from USB or battery. Earlier ADC-cost what-if estimates omit that startup supply, and cheaper GH/ESD substitutions remain unapplied; they must not be presented as the cost of this actual schematic. Review/BOM files are generated locally. The complete product BOM and INR200 target remain unresolved.
