# Main board Rev B — cost estimate

Catalogue snapshot 2026-09-27 (PCBParts JLC/LCSC, `price-snapshot-2026-09-27.json`), USD, INR at 96/USD. Default TFT + SEN5x/SEN6x build; DNP parts (the SCD41 U8 and the J6/J8 headers) excluded; the CO2 supply (U7, C15, C16, C42) is fitted. JLCPCB Standard PCBA, double-sided (buttons on the front, everything else including USB-C on the back). Not a quotation.

Solder joints per board: 222 SMT, 6 through-hole. 33 unique placed parts.

| Per board | 5 prototypes | 1000 boards |
|---|---:|---:|
| Parts | $5.95 (INR 572) | $4.01 (INR 385) |
| PCB fabrication (2-layer, 47 x 76 mm) | $0.40 (INR 38) | $0.13 (INR 12) |
| Assembly (setup, stencil, feeders, joints) | $24.78 (INR 2378) | $0.49 (INR 47) |
| **Total** | $31.13 (INR 2988) | $4.63 (INR 444) |

Excludes shipping, import duty and GST, programming/test, the display, PM/CO2 sensors, enclosure and the battery board. JLC may add attrition parts; small orders also pay per-order minimums.

## Parts at 1000 boards

| Refs | Part | LCSC | Library | Qty | Unit $ | Line $ |
|---|---|---|---|---:|---:|---:|
| U1 | ESP32-C3-MINI-1-H4X | C41349510 | extended | 1 | 2.1209 | 2.121 |
| J5 | TFT TOP CONTACT | C3168738 | extended | 1 | 0.4418 | 0.442 |
| C10,C13 | 22uF 10V | C45783 | basic | 2 | 0.1116 | 0.223 |
| C2,C7,C9,C12,C16 | 10uF 25V | C15850 | basic | 5 | 0.0442 | 0.221 |
| U4 | TPS22917DBVR | C2681320 | extended | 1 | 0.1967 | 0.197 |
| U7 | TPS7A2033PDBVR | C2862740 | extended | 1 | 0.1207 | 0.121 |
| C1,C15 | 1uF 16V | C15849 | basic | 2 | 0.0543 | 0.109 |
| U5,U6 | SY8089A1AAC | C479074 | extended | 2 | 0.0520 | 0.104 |
| L1,L2 | 2.2uH SWPA4020S | C83423 | extended | 2 | 0.0442 | 0.088 |
| Q1 | AO3400A | C20917 | basic | 1 | 0.0520 | 0.052 |
| J1 | USB-C / standalone | C49287211 | extended | 1 | 0.0470 | 0.047 |
| J3 | SEN5x / 5V | C51940119 | extended | 1 | 0.0434 | 0.043 |
| SW4 | POWER / MSK12C02 | C431540 | extended | 1 | 0.0410 | 0.041 |
| J4 | SEN6x / 3.3V | C51940118 | extended | 1 | 0.0359 | 0.036 |
| D1 | USBLC6-2SC6 | C2827654 | extended | 1 | 0.0309 | 0.031 |
| C3,C11,C14 | 100nF 25V | C14663 | basic | 3 | 0.0073 | 0.022 |
| D2 | B5819W | C8598 | basic | 1 | 0.0192 | 0.019 |
| SW1 | LEFT | C318884 | basic | 1 | 0.0138 | 0.014 |
| SW2 | OK | C318884 | basic | 1 | 0.0138 | 0.014 |
| SW3 | RIGHT | C318884 | basic | 1 | 0.0138 | 0.014 |
| R15,R17,R19,R27 | 100kR | C25803 | basic | 4 | 0.0024 | 0.010 |
| J2 | BAT PWM / Dupont | C32713268 | extended | 1 | 0.0088 | 0.009 |
| C8 | 1nF 25V | C1588 | basic | 1 | 0.0068 | 0.007 |
| R1-R4,R33 | 10kR | C25804 | basic | 5 | 0.0013 | 0.006 |
| R21,R22 | 4.7kR | C23162 | basic | 2 | 0.0022 | 0.004 |
| C42 | 100nF 16V | C1525 | basic | 1 | 0.0034 | 0.003 |
| R20 | 22kR | C31850 | basic | 1 | 0.0031 | 0.003 |
| R28 | 33R | C25375 | extended | 1 | 0.0027 | 0.003 |
| R7,R8 | 22R | C23345 | basic | 2 | 0.0013 | 0.003 |
| R16 | 100R | C22775 | basic | 1 | 0.0025 | 0.003 |
| R5,R6 | 5.1kR | C23186 | basic | 2 | 0.0012 | 0.002 |
| R34 | 1kR | C21190 | basic | 1 | 0.0020 | 0.002 |
| R18 | 23.2kR | C49656146 | extended | 1 | 0.0011 | 0.001 |
