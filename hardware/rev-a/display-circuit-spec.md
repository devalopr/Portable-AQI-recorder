# Display circuit specification (research input)

Status: source-backed implementation input; not yet released as a KiCad schematic. Prepared 2026-09-07.

## Sources

- Good Display, **GDEY037T03-T02**, product specification revision shown on the supplied PDF as 2022-06-16 rev 1.0; the current vendor file listing also exposes a 2025-01-08 specification download: <https://www.good-display.com/comp/portalResCompanyFile/relatedlist.do?$!=&appId=24&compId=portalResCompanyFile_relatedlist-15877162676116817&detailAppId=2&detailId=437>.
- Readable mirror of the vendor PDF used to inspect pages 6, 7 and 35: <https://ecksteinimg.de/Photo/GD03042/GDEY037T03-T02.pdf?_t=1768267937>.
- Good Display page-35 reference circuit is reproduced in the PDF as “10. Reference Circuit”. The corresponding vendor text lists component requirements but not all values; use the circuit drawing for values and the panel/vendor for final approval.
- KiCad 10 installed footprint library contains `Connector_FFC-FPC:TE_1-84952-0_1x10-1MP_P1.0mm_Horizontal`.

## Panel interface

The Good Display drawing calls the panel connector P1 and specifies 24 pins at 0.5 mm pitch. The table below is the vendor numbering and logical signal contract. It is the panel-side number order; the main-board footprint must be checked against the connector manufacturer's mating view.

| P1 pin | Vendor name | Type / connection for this design |
|---:|---|---|
| 1 | NC | Leave open; do not join to other NC pins |
| 2 | GDR | Charge-pump MOSFET gate-drive control; connect to Q1 gate as shown in reference circuit |
| 3 | RESE | Current-sense input for control loop; connect to Q1 source/current-sense network as shown |
| 4 | VGL | Negative gate-drive rail; connect to C1 and the panel boost network |
| 5 | VGH | Positive gate-drive rail; connect to C2 and the panel boost network |
| 6 | TSCL | Optional external temperature-sensor I²C clock; leave open unless an external sensor is fitted |
| 7 | TSDA | Optional external temperature-sensor I²C data; leave open unless an external sensor is fitted |
| 8 | BS | Bus-interface selection; the inspected page-35 reference ties this pin to GND. Keep a solder-jumper provision to +3V2 because the page-7 interface table and panel revision must agree before release. |
| 9 | BUSY | Panel busy output to MCU GPIO; high means operation/temperature-sensor communication is in progress |
| 10 | RES# | Active-low panel reset from MCU |
| 11 | D/C# | SPI data/command select from MCU; high=data, low=command |
| 12 | CS# | Active-low SPI chip select from MCU |
| 13 | SCLK | SPI serial clock from MCU |
| 14 | SDA | SPI serial data (MOSI; also readback pin where used) |
| 15 | VDDIO | Interface logic supply; +3V3 |
| 16 | VCI | Panel IC supply; +3V3 in the vendor reference circuit |
| 17 | VSS | Ground |
| 18 | VDD | Core logic supply; decouple to VSS and follow the vendor circuit |
| 19 | VPP | Leave open in the inspected reference circuit; no C8 is fitted |
| 20 | VSH1 | Positive source-drive rail; decouple to VSS |
| 21 | GVGH/PREVGH | Positive gate-drive rail; connect to D3 output/C5 node and panel decoupling |
| 22 | VSL | Negative source-drive rail; decouple to VSS |
| 23 | VGL/PREVGL | Negative rectifier output node; connect to D1/C11 node, distinct from pin 4 VGL |
| 24 | VCOM | Common electrode drive rail; decouple to VSS |

The source table labels pin 2 as GDR and pin 3 as RESE, while the reference drawing labels the associated control nodes `GDR` and `RESE`. Do not reinterpret `RESE` as the digital `RES#` reset pin; they are separate pins (3 and 10).

The UC8253 supports 3-wire and 4-wire SPI. The inspected page-35 reference ties BS low; provision a jumper so the production panel revision can be configured after reconciling the page-7 interface table. Use separate CS#, D/C#, SCLK and SDA. The vendor warns to return CS# high every 8 bits. The panel is 240 × 416 active pixels (the product page sometimes writes 416 × 240 depending on orientation).

## Vendor reference circuit to reproduce

The page-35 circuit is a discrete boost/charge-pump network feeding the bare panel. It is not optional when using the bare panel: a simple 3.3 V connector carrying only SPI and logic power is insufficient.

### Input and boost network

Use +3V3 as the input rail. The drawing shows:

| Ref | Vendor-drawn value / type | Connection intent |
|---|---|---|
| C4 | 4.7 µF / 50 V | +3V3 to GND at boost input |
| L1 | 10 µH, 1 A | +3V3 to boost switching node |
| C3 | 4.7 µF / 50 V | Flying capacitor between the switching node and the negative-pump node |
| Q1 | Si1308EDL | MOSFET controlled by GDR/RESE network |
| R1 | 1 MΩ | GDR bias to GND |
| R2 | 0.47 Ω | RESE current-sense resistor to GND |
| D1–D3 | MBR0530 | Charge-pump/rectifier diodes; ≥30 V reverse, ≥500 mA, forward drop ≤430 mV |
| C1 | 1 µF / 50 V | Pin-4 VGL reservoir/filter capacitor; do not merge with pin-23 PREVGL |
| C2 | 1 µF / 50 V | VGH reservoir/filter capacitor |
| C5 | 1 µF / 50 V | PREVGH reservoir/filter capacitor |

The vendor's component requirement table calls for C1–C12 in 0603/0805, X5R/X7R, voltage rating ≥25 V; R1/R2 in 0603/0805, 1% and ≥0.05 W; Q1 equivalent with VDS ≥30 V, VGS(th) ≤1.5 V and RDS(on) ≤400 mΩ; and L1 equivalent with 1 A capability. The drawing itself uses 50 V capacitors, which should be retained for margin on the boosted rails.

### Panel rail decoupling

The reference drawing shows 1 µF / 50 V capacitors from each generated panel rail to VSS:

| Ref | Rail |
|---|---|
| C6 | VCI / logic supply node as drawn |
| C7 | VDD |
| C8 | No capacitor fitted in the inspected reference; pin 19 VPP remains open |
| C9 | VSH1 |
| C10 | GVGH / PREVGH node |
| C11 | VSL / PREVGL negative rectifier node |
| C12 | VCOM |

The page-35 image was inspected at full resolution. D1 is K=negative-pump node, A=PREVGL; D2 is K=GND, A=negative-pump node; D3 is K=PREVGH, A=boost switching node. The negative-pump node is the C3 flying-capacitor return. Perform a symbol-pin/netlist comparison against the panel drawing before release. Do not substitute a generic e-paper boost circuit or infer rail polarity from the label alone.

## TFT 10-pin flex connector candidate

The supplied LCD PDF/design brief identifies a 10-contact flex at 1.00 mm pitch, 11 mm nominal flex width, 0.3 mm stiffened thickness, and 9 mm first-to-last contact span. The contact face is not identified in the local PDF, so the mating side remains a mechanical release blocker.

Preferred footprint candidate for the main-board rear/top-wrapped LCD tail:

`TE Connectivity 1-84952-0`, 10 positions, 1.00 mm pitch, right-angle SMT, bottom-contact ZIF, 0.3 mm FPC, 1 A contact rating. TE's product page identifies it as “1MM FPC HORZ.BTTM CONT.ASS.10P” and gives 17.92 mm × 6.54 mm × 2.56 mm nominal body envelope: <https://www.te.com/en/product-1-84952-0.html>. Digi-Key confirms bottom contact, 10 positions, 1.00 mm pitch and right-angle SMT: <https://www.digikey.in/en/products/detail/te-connectivity-amp-connectors/1-84952-0/2180591>.

KiCad footprint match:

`Connector_FFC-FPC:TE_1-84952-0_1x10-1MP_P1.0mm_Horizontal`

The connector is a ZIF/stuffer actuator and mechanically fits the local dimensions better than a guessed JST wire connector. It is not a locking wire-to-board connector; its flex lock is the retention mechanism. Before placing it on the rear, verify the actual LCD sample's exposed-copper face, stiffener thickness and pin-1 orientation. If the panel contact face is top rather than bottom for the selected routing orientation, use a top-contact equivalent or flip the flex routing; do not mirror the footprint by assumption.

## Adapter fallback and release boundary

Good Display lists the DESPI-C02 family as a matched development kit/adapter. It is suitable for bench bring-up because it provides the vendor controller/power implementation, but it is not a substitute for the integrated main-board circuit in the final bare-panel assembly. If the full page-35 circuit cannot be transferred and reviewed, reserve a 24-pin 0.5 mm panel connector plus an external adapter footprint/header as a bring-up-only option and mark the e-paper population DNP. Do not claim that the main board can drive GDEY037T03 until the boost rails, pinout, and a UC8253-compatible driver have been bench tested.

## Remaining mechanical/electrical release blockers

1. Confirm LCD 10-pin contact-face orientation and pin-1 marking from the physical sample; the local LCD PDF does not establish it.
2. Confirm whether the selected GDEY037T03 purchase revision is the T02 panel represented by the current 45-page PDF; do not mix the pinout with the newer FT21 front-light/touch variant.
3. Verify all 24-pin 0.5 mm panel contacts and page-35 rail connections in the KiCad netlist before schematic release. The passive values and vendor topology above are sufficient for a first capture, but this is still a source review input rather than a validated electrical design.
