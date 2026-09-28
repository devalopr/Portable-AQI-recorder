# Local 3D models (Rev B main)

The footprints reference these files through `${KIPRJMOD}/lib/3d/`.

| File | Used by | Source |
|---|---|---|
| `USB-C-SMD_TYPE-C-16P-L6.5.step` | J1 | LCSC/EasyEDA catalogue model for C49287211, imported with easyeda2kicad 1.0.1 for the battery board and copied from the battery board's `integrated-power/lib/AQI_Power.3dshapes/`. Footprint offset (0, −1.584, 1.168) as on the battery board. |
| `TFT_2.4in_ST7789_10P_Panel.step` + `.py` | DS1 (board-only) | Generated. 42.72 × 60.26 × 2.5 mm panel, 36.72 × 48.96 mm active area, 12 mm flex wrapped over the top edge into J5. The active-area offsets and flex path are typical values; see the source docstring. |
| `SW_Push_1P1T_XKB_TS-1187A.step` + `.py` | SW1–SW3 | Generated simplified envelope: 5.1 × 5.1 × 1.5 mm, 2.0 mm actuator. |
| `SW_SPDT_Shouhan_MSK12C02.step` + `.py` | SW4 | Generated simplified envelope: 6.7 × 2.8 × 1.4 mm shell, actuator out of the right edge. |
| `ESP32-C3-MINI-1.step` | U1 | Carried over from Rev A. |
| `Sensirion_SCD4x.step` | CO₂ option | Official [Sensirion model](https://sensirion.com/media/documents/260AFF2D/616531AE/Sensirion_CO2_Sensors_SCD4x_STEP_file.step), +0.829 mm Z offset. |
| `SW_SPDT_CK_JS102011SAQN.step` + `.py` | — | Rev A power switch, no longer used. |

Regenerate a generated model with the CAD skill: `scripts/step lib/3d/<name>.py`. The generated models are dimension envelopes, not manufacturer models; use the datasheets for release checks.

Optional parts keep their DNP flags. Enable "Show DNP footprints" in KiCad's 3D viewer to see them.
