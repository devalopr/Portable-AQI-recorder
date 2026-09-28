# Common power-stage architecture estimate

2026-09-12. 1,000 boards per variant, INR96/USD. This is not a schematic-derived BOM or supplier quote.

| Candidate | MPN / LCSC | INR per board | Status |
|---|---|---:|---|
| Integrated charger/boost | IP5310_I2C / C20616661 | 31.72 | OUT OF STOCK; replenishment quote required |
| MCU | CH32V003F4P6 / C5187096 | 15.62 | existing selection |
| 3.3V buck IC | SY8089A1AAC / C479074 | 5.20 | existing candidate |
| Input USB-C | TYPE-C 16PIN 2MD(073) / C2765186 | 4.86 | footprint pending |
| Output USB-C | TYPE-C 6P / C456012 | 2.27 | USB port implementation under review |
| GH connector | SM10B-GHS-TB / C2683602 | 18.74 | genuine JST retained in estimate |
| USB data ESD | USBLC6-2SC6-ES / C5180249 | 2.16 | unqualified lower-cost candidate |
| Input CC detector | HUSB320-BA000-QN12R / C7471906 | 18.89 | retained conservatively; possible integration saving NOT deducted |
| Input limiter | SY6280AAAC / C207620 | 5.69 | input-current range/thermal qualification pending |
| Output CC + switch | HUSB305-01 / C7471917 | 19.52 | candidate for 1.5A/3A USB advertisement; not applied |

Catalogue-candidate subtotal: **INR124.67**, without holder or the categories below.

| Unquoted engineering allowance | INR low | INR high |
|---|---:|---:|
| Two inductors, power capacitors and remaining decoupling | 12 | 26 |
| Protection IC, power/signal MOSFETs, resistors, optional NTC provision | 8 | 18 |
| Three-position selector and dim RGB LED | 4 | 10 |
| Two-layer bare PCB: one-cell geometry | 6 | 12 |
| Assembly including holder, setup and attrition amortized | 10 | 25 |
| Programming and functional test | 5 | 12 |

Holder allowance: INR30 per holder from user sourcing. Two-cell estimate assumes two separate holders and INR4–10 additional PCB allowance.

| Variant | Estimated assembled cost, INR |
|---|---:|
| 1 cell(s) | 199.67–257.67 |
| 2 cell(s) | 233.67–297.67 |

**These ranges are planning estimates, not cost guarantees.** Multiple parts are unqualified, the selected integrated variant has zero catalogue stock, and all manufacturing allowances are unquoted. No INR200 factory-cost claim is established.

Potential savings not deducted: integrating input CC detection, qualifying a cheaper GH-compatible connector, further passive consolidation and assembly quotation. Do not remove electrical functions solely to make the spreadsheet reach the target.

Excludes cells, enclosure, cables, packaging, freight, tax, certification, development and prototypes. Original BOM handoff metadata and all KiCad files are unchanged.
