# Video 351 candidate review — existing features only

User requested comparison of TP4056, TP5000, CN3065, TP5602, AP2016, FP6298 and MT3608. Solar, LiFePO4, RTC and precision current monitoring are explicitly out of scope. This is a selection review, not a schematic change or hardware qualification.

Retain 1-cell 5V/2A total (USB-C advertises 1.5A), 3.3V/1A auxiliary within the shared power budget, approximate PWM percentage, MCU/RGB, 0.5/1/1.5A charge selector with source-current limits, USB data pass-through, genuine GH, cell protection and small two-layer construction. The intended two-parallel-cell 3A variant remains a separate qualification target.

## Findings

| Candidate | Evaluation against retained requirements | Decision |
|---|---|---|
| TP4056 | Linear charger, up to 1A. Misses 1.5A charge setting; requires separate boost. At 5V input and 3.2V battery, 1A would dissipate approximately 1.8W before thermal regulation. | Reject for this specification, even if a cheaper second-source version is available. |
| CN3065 | Linear charger up to 1A; input-adaptive/solar capability offers no benefit for this scope. Separate boost required. | Reject for 1.5A charging. No in-stock catalogue match found; this is not proof of global unavailability. |
| TP5000-QFN16 | Switching charger up to 2A; resistor-adjustable current makes the selector feasible. Charger only: needs separate boost, second inductor, rectifier and current-sense parts. | Electrically relevant fallback, not a demonstrated cost saving. |
| TP5000X-4.2-ESOP8 | Slightly cheaper related charger, not pin-compatible with QFN16; exact variant must be validated separately. The cheaper 4.35V SKU is unsuitable for ordinary 4.2V cells. | Alternative charger candidate only; not adopted. |
| FP6298XR-G1 | Boost only. Manufacturer describes a 4.5A internal switch; that is not 5V/4.5A output. Catalogue synchronous-rectifier metadata must not replace review of the manufacturer application circuit. | With TP5000, costs more in ICs alone than IP5310. Not selected. |
| MT3608 | Boost only, with external Schottky. Manufacturer lists 4A typical switch-current limit, no guaranteed minimum in the table. At 3.0V and assumed 90% efficiency, 5V/2A requires 3.70A average input before ripple; 5V/3A requires 5.56A. Limited margin for one-cell full-discharge operation and unsuitable as the common 3A solution. | Reject as a confidently rated replacement; cheap IC alone does not establish output performance. MT3608L/B are different parts. |
| TP5602 | Integrated switching charger/boost, external input PMOS and switching NMOS, resistor-set current. Relevant competing architecture. Manufacturer documents nominal light-load auto-off (~50mA/~10s), charge/boost mode switching, and differing 2.5A/3A headline ratings across documents. Continuous low-load output and 3A performance need exact-revision validation. Battery-fed MCU bypasses PMIC shutdown, so external cell protection cannot simply be deleted. | Screened, not selected: no demonstrated cost saving or stocked procurement source. |
| AP2016 | Video's original vendor link failed. Searches did not establish a trustworthy manufacturer datasheet or orderable exact IC; many results are unrelated Hammond enclosure panels. | Unresolved sourcing/documentation; do not assign ratings or a guessed price. |

## Exact-part IC prices

1,000 boards, one IC of each type per board, applicable quantity tier, INR96/USD planning exchange rate. This is a catalogue snapshot, not a quote or complete circuit cost. Raw responses are in video-351-candidate-pricing-2026-09-20.json.

| Part | LCSC | Applicable USD price | INR | Catalogue stock |
|---|---|---:|---:|---:|
| TOPPOWER TP4056-42-ESOP8 | C16581 | 0.1107 (500+) | 10.63 | 94393 |
| TP5000-QFN16 | C51699 | 0.2133 (500+) | 20.48 | 7232 |
| TP5000X-4.2-ESOP8 | C5447152 | 0.1970 (500+) | 18.91 | 11604 |
| FP6298XR-G1 | C88319 | 0.2344 (1000+) | 22.50 | 6449 |
| MT3608 | C84817 | 0.0801 (1000+) | 7.69 | 180594 |
| TP5602 | C80366 | 0.3239 (1000+) | 31.09 | 0 |
| Existing IP5310_I2C baseline | C20616661 | 0.3304 (1000+) | 31.72 | 0 in existing cost snapshot |

TP5000 + FP6298: INR42.98 IC-only, INR11.26 above the existing PMIC, before extra charger passives, inductor, rectifiers and assembly. TP5000X pair: INR41.41. TP5602 saves only INR0.62 on PMIC unit price before accounting for its external power devices and other circuit differences. No full replacement BOM or lower assembled-board cost has been established. Keep current conditional INR289–317 estimate; INR200 remains unachieved.

The MCU for PWM battery reporting and the 3.3V converter remain necessary with every candidate here. None of the reviewed evidence establishes replacement of USB-C CC handling, BC1.2 detection/data switching or host current-allocation logic. Input-voltage droop regulation is not USB enumeration or charger classification. Do not book those components as savings without a verified replacement function.

## Sources

- Video: https://youtu.be/-SJbdPvgQnE (description and captions reviewed).
- TP4056 manufacturer: https://www.toppwr.com/uploadfile/file/20230304/640301eae1260.pdf
- TP5000 manufacturer: https://www.toppwr.com/uploadfile/file/20240913/66e3cd182a1c6.pdf
- TP5000 demo BOM: https://www.toppwr.com/uploadfile/file/20230221/63f45148cc8e5.pdf
- TP5000X manufacturer page: https://www.toppwr.com/eproduct/view.php?id=481
- CN3065 manufacturer datasheet mirror: https://uelectronics.com/wp-content/uploads/2019/10/DSE-CN3065.pdf
- FP6298 manufacturer application note mirror: https://dianyuan-public.oss-cn-shenzhen.aliyuncs.com/community/2021/11/60030202111221532549860.pdf
- MT3608 manufacturer datasheet mirror: https://www.olimex.com/Products/Breadboarding/BB-PWR-3608/resources/MT3608.pdf
- TP5602 manufacturer English document: https://www.toppwr.com/uploadfile/file/20240913/66e3a58fd5b38.pdf
- TP5602 original manufacturer Chinese document, indexed excerpt retrieved: https://www.tp-asic.com/res/tp-asic/pdres/201609/TP5602.pdf
- TP5602 catalogue: https://jlcpcb.com/partdetail/TOPPOWER-TP5602/C80366
- AP2016 original video link (failed retrieval): http://www.zm699.com/Products/10agglmdtb.html

## Result

Retain IP5310-I2C provisionally, not because it is proven globally cheapest, but because these seven alternatives do not establish a cheaper feature-equivalent circuit. IP5310 sourcing and outstanding circuit qualification remain unresolved. Revisit TP5602 only with a firm supplier quote and exact-datasheet validation. No additional video features, schematic changes, BOM substitutions or PCB routing were introduced.
