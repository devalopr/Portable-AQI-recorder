# Cost reduction before schematic/layout release

Target: under INR200 assembled, excluding cell. Scope remains one-cell 5V/2A (USB-C 1.5A) and two parallel cells 5V/3A (USB-C 3A), common power components, 3.3V/1A sharing the power budget, PWM battery percentage, RGB and three-position charging selector.

All prices below use 1,000 units and the existing planning conversion INR96/USD. These are catalogue snapshots, not manufacturing quotations. No electrical KiCad files or assembly BOM metadata changed in this review.

## Recommended cost direction

1. Investigate removing the **input HUSB320**, using the existing CH32 MCU ADC to classify CC1/CC2. The IC costs INR18.8928. Reserve an additional, unquoted INR2–5 for the incremental analog/protection circuitry; provisional net saving INR13.89–16.89. Keep the input current limiter in the estimate. No second MCU is required.
2. Retain **HUSB305-01** on the output at INR19.5168 for now: it combines CC attachment/current advertisement with the output power switch and limiting. Replacing it with an ADC does not eliminate the need for those other functions. Its 1.5A/3A settings support our two variants without USB PD.
3. Qualify a cheaper actual locking GH-compatible board header. **Lingqiang LQ-GH1.25-10PWT / C54618749** is USD0.0529 at the 300+ tier (INR5.0784), versus genuine JST INR18.7392: potential saving INR13.6608. Observed stock 5,225. Manufacturer drawing, latch compatibility, mating contacts, polarity and current/temperature rise still need verification; not a drop-in approved replacement.

Microchip explicitly demonstrates MCU ADC reading CC voltages to identify a source's advertised current in its power-bank reference design, section 1.3.1.2. This establishes feasibility, not verification of a CH32 implementation:

- [Microchip MIC2877 reference design](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/UserGuides/50002984A.pdf)
- [ST ADC-based Type-C source implementation](https://wiki.st.com/stm32mcu/wiki/STM32StepByStep:Getting_started_with_USB_Type-C_only_Source)

Input implementation gates: correct independent Rd terminations; ADC input range and leakage across supply states; reference accuracy and conservative thresholds; debounce and changes to source advertisement; USB default-current/enumeration policy; conservative reset/watchdog current limiting; dead-cell recovery without relying on a powered MCU; no USB-data interference. Firmware and bench verification effort is additional development cost, not included in recurring component savings.

## Other options checked

| Candidate | Catalogue IC cost INR | Finding |
|---|---:|---|
| HUSB320 input CC | 18.89 | Baseline; removal more promising than another dedicated CC chip |
| WUSB3801Q-12/TR, C2931342 | 21.98 | More expensive at applicable 500+ tier |
| FUSB303BTMX, C895444 | 26.41 | More expensive at 1000+ tier |
| IP5310_I2C, C20616661 | 31.72 | Leading common-stage candidate; zero stock, reset/control and continuous-current qualification unresolved |
| IP5356M_LBZ_CB, C46550232 | 55.94 | Higher IC price; evaluate total circuit only if integrated ports remove enough other parts; control documentation unresolved |
| ETA9740, C7465512 | 14.70 | Cheaper, but 2.4A boost does not meet the two-cell 3A requirement |
| IP5328P | Not established | No in-stock exact part in search; not budgeted using unrelated assembly-service SKU prices |

IP5310's built-in CC is another possible way to remove external circuitry, but one integrated port cannot automatically control both physical connectors. Its documented control/reset behavior must establish safe input-only operation or selectable 1.5A/3A output operation before any such saving is counted. Do not add that saving to the input-ADC saving: they are alternative implementations of the same function.

A second low-price connector, **Hanxia HX 1.25-10P WT / C5343061**, is INR3.9264 at quantity 1000. Its downloaded manufacturer drawing does show a PCB header, but its 17.5mm overall dimension and shape differ from the GH candidate. Catalogue GH classification is insufficient evidence of locking/mating compatibility; **not counted**. HanElectricity 1251H-10P also has inconsistent catalogue metadata and is not counted.

## Reproducible estimate, not a cost guarantee

Run `python3 hardware/rev-b/scripts/prelayout_budget.py`. Baseline remains separately recorded. New scenarios are in `cc-cost-scenarios.json`.

| Assembled planning range, INR | One cell | Two cells |
|---|---:|---:|
| Previous integrated-stage estimate | 199.67–257.67 | 233.67–297.67 |
| MCU input CC, genuine JST | 182.78–243.78 | 216.78–283.78 |
| MCU input CC plus candidate Lingqiang GH | 169.12–230.12 | 203.12–270.12 |

Holder allowance is INR30 each; two-cell estimate assumes two separate holders. Remaining power passives, protection, switch/LED, PCB, assembly, programming and test are still unquoted allowances. These ranges exclude cells, enclosure, cables, packaging, freight, tax, certification and development. Existing cheaper USB ESD and integrated output-controller savings were already counted in the previous estimate and are not counted twice here.

Conclusion: INR200 is a plausible one-cell target with these changes, not an established maximum. Two-cell below INR200 is not supported by this estimate. Need exact remaining component selections, supplier stock confirmation and assembled quotations before declaring the cost target met. Circuit, schematic and cost validation still precede placement/routing.
