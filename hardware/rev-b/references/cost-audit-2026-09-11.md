# Catalogue cost audit — 2026-09-11

Layout completion paused for cost review at user request. These are indicative PCBParts/LCSC catalogue prices, not a quantity-qualified production quote. INR conversions use a rounded planning rate of INR96/USD (market lookup approximately95.7). No completed low-cost production BOM is claimed.

| Ref | Current part | USD each | INR planning |
|---|---|---:|---:|
| U1 | ETA6003Q3Q | 0.5183 | 49.8 |
| U2 | TPS61023DRLR | 0.2657 | 25.5 |
| U3 | SY8089A1AAC | 0.0879 | 8.4 |
| U4 | CH32V003F4P6 | 0.2879 | 27.6 |
| U6 | HUSB320-BA000-QN12R | 0.4046 | 38.8 |
| U7 | TUSB320LAIRWBR | 1.0691 | 102.6 |
| U8 | TPS2552DBVR | 0.3333 | 32.0 |
| U11 | SY6280AAAC | 0.0990 | 9.5 |
| J1 | 12401610E4#2A | 1.3420 | 128.8 |
| J7 | USB4135-GF-A | 0.8822 | 84.7 |
| J3 | SM10B-GHS-TB | 0.4387 | 42.1 |

**Partial subtotal only: USD5.7287, approximately INR550.**

Excluded: holder, all three inductors, charge selector, RGB, protection IC/FET, small transistors, ESD protection, passives, PCB, assembly/programming/test, freight, tax and margin. The present draft cannot support a small-premium retail product near the INR198 reference at these procurement prices.

Additional outliers: catalogue search for XAL5030-102MEC returned USD8.2028 and XAL4020-222MEC USD10.7421 each (two fitted). These unusually expensive sourcing entries must not be used as representative mass-production magnetics prices. Replace with electrically qualified low-cost inductors and obtain quantity-specific quotations. Keystone1042 and PCM13SMTR remain premium/unquoted choices; the actual generic holder footprint is still unresolved.

Next cost work: integrated or cheaper output CC/load switching; economical USB-C receptacles and verified generic holder; qualified inexpensive inductors; quantity-priced switch and MCU; single electronics-face assembly including RGB. Preserve protected-cell power path, safe charge-current startup, selectable 0.5/1/1.5A charging, no low-load auto-off, PWM, and shared 5V/3.3V output budget.

Do not finish a fabrication release before resolving the costed architecture and output-current qualification. Current power-stage ratings remain engineering targets, not validated product specifications.

## Correction: connector sourcing is not cost-optimized

The INR255 figure priced specific branded parts still in the draft, not reasonable low-cost production choices. It must not be used to imply USB-C connectors inherently cost that much. Price source: PCBParts `jlc_search`, not a JLC assembly quotation or verified bulk tier.

Fresh alternative search:
- SHOU HAN TYPE-C 16PIN 2MD(073), C2765186: USD0.0743 indicative unit price.
- SHOU HAN TYPE-C16PIN, C393939: USD0.0686.
- SHOU HAN TYPE-C 6P, C456012: USD0.0387 (power-only; not a replacement for the input data connector).
- Genuine JST SM10B-GHS-TB, C2683602: USD0.4387.

Using C2765186 + C456012 gives about INR11 for the two USB-C receptacles, or INR53 including the existing genuine JST GH, before fees/tax. These are candidates, not already-validated footprint substitutions. Any GH-compatible alternative must have verified latch/mating dimensions and must not be labelled genuine JST. The specific USD0.025 volume tier mentioned by the user has not been independently verified.

Replacing only these two USB entries lowers the selected-parts partial subtotal from about INR550 to INR347; this remains an incomplete catalogue subtotal, not a finished-board estimate. The entire design needs quantity-specific low-cost sourcing, including ICs and magnetics. Premium prototype selections should have been corrected before presenting a production-cost implication.
