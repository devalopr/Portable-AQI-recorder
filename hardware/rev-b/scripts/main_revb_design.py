"""Rev B main board: USB-C is the only power/data input; battery % arrives as PWM on a Dupont header.

Starts from the routed Rev A design (kept in ../main/review/rev-a-baseline) and edits design.json, then regenerates
the schematic. The PCB is revised separately by main_revb_board.py so Rev A routing is preserved.
"""
from pathlib import Path
import json, copy
from kicad_common import Project

root = Path(__file__).resolve().parents[1]
src = root / 'main/review/rev-a-baseline/design.json'     # the routed Rev A design this revision starts from
out = root / 'main'
d = json.loads(src.read_text())
C = {c['ref']: c for c in d['components']}

# GH link, USB data mux, power mux and their helpers are gone: the battery board now forwards
# power and USB data through its USB-C output into J1, and sends battery % as PWM.
removed = ['J2', 'U2', 'U3', 'Q1', 'Q2', 'Q4', 'R9', 'R10', 'R11', 'R12', 'R13', 'R14',
           'C4', 'C5', 'C6', 'R24', '#FLG2']
d['components'] = [c for c in d['components'] if c['ref'] not in removed]

rename = {'+5V_USB': '+5V_SYS', 'USB_LOCAL_D+': 'USB_D+', 'USB_LOCAL_D-': 'USB_D-',
          'USB_SWITCH_D+': 'USB_D+', 'USB_SWITCH_D-': 'USB_D-'}
for c in d['components']:
    c['nets'] = {k: rename.get(v, v) for k, v in c['nets'].items()}

# GPIO21 (former UART TX) receives battery PWM through R34; R33 is the host-side pull-up.
C['U1']['nets']['31'] = 'BAT_PWM_MCU'
C['TP4'].update(value='BAT_PWM_MCU', nets={'1': 'BAT_PWM_MCU'})
# OK button doubles as the BOOT button on GPIO9 (R2 pull-up); MCP23008 INT wakes GPIO2.
C['SW2']['nets']['1'] = 'BOOT_GPIO9'
C['U9']['nets'].update({'11': None, '8': 'BOOT_GPIO2'})

j2 = dict(ref='J2', lib='Connector_Generic:Conn_01x02', value='BAT PWM / Dupont',
          nets={'1': 'GND', '2': 'BAT_PWM'}, sch=[393, 53], xy=None, rot=0.0, side='back', dnp=False,
          fp='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical', mpn='2.54mm 1x02 pin header',
          note='Matches battery board J9: pin 1 GND, pin 2 BAT_PWM. Straight female-female jumper.')
d['components'].append(j2)
for ref, value, nets, sch in [('R33', '10kR', {'1': '+3V2', '2': 'BAT_PWM'}, [470, 300]),
                              ('R34', '1kR', {'1': 'BAT_PWM', '2': 'BAT_PWM_MCU'}, [515, 300])]:
    c = copy.deepcopy(C['R17'])
    c.update(ref=ref, value=value, nets=nets, sch=sch, xy=None, mpn='', manufacturer='',
             note='Battery PWM receiver: pull-up to +3V2 and GPIO21 boot-UART contention limiting.')
    d['components'].append(c)

# ---- Cost-down (2026-09-27, user-approved): same functions, cheaper / JLC-stocked parts. ----
C = {c['ref']: c for c in d['components']}
drop = ['U9', 'C17', 'R23', 'R25', 'U10', 'C19', 'C18', 'R26']
d['components'] = [c for c in d['components'] if c['ref'] not in drop]
d['custom_symbols'].append({'name': 'SY8089A1', 'pins': [
    {'number': 1, 'name': 'EN', 'type': 'input', 'side': 'left'},
    {'number': 2, 'name': 'GND', 'type': 'power_in', 'side': 'bottom'},
    {'number': 3, 'name': 'LX', 'type': 'output', 'side': 'right'},
    {'number': 4, 'name': 'IN', 'type': 'power_in', 'side': 'left'},
    {'number': 5, 'name': 'FB', 'type': 'input', 'side': 'right'}]})
# Buttons straight to the strap GPIOs (each already has a 10k pull-up): LEFT GPIO8, OK GPIO9, RIGHT GPIO2
# (LEFT sits beside the GPIO8 pin; GPIO2 reaches RIGHT along the front under the buttons).
C['SW1']['nets']['1'] = 'BOOT_GPIO8'
C['SW3']['nets']['1'] = 'BOOT_GPIO2'
# SY8089A1 bucks (VOUT = 0.6 V x (1 + RH/RL)); optional datasheet Cff omitted for cost. EN tied to VIN.
for u, sw, fb in [('U5', 'CORE_SW', 'CORE_FB'), ('U6', 'PM_SW', 'PM_FB')]:
    C[u].update(lib='AQI:SY8089A1', value='SY8089A1AAC', fp='Package_TO_SOT_SMD:SOT-23-5',
                nets={'1': '+5V_SW', '2': 'GND', '3': sw, '4': '+5V_SW', '5': fb},
                mpn='SY8089A1AAC', manufacturer='Silergy')
C['R17']['value'] = '100kR'; C['R18']['value'] = '23.2kR'     # +3V2 = 3.19 V (TFT margin kept)
C['R19']['value'] = '100kR'; C['R20']['value'] = '22kR'       # +3V3_PM = 3.33 V
# Backlight: low-side AO3400A switch; R28 sets LED current from +5V_SW (validate brightness on the panel).
C['R28'].update(value='33R', fp='Resistor_SMD:R_1206_3216Metric',
                note='Backlight series resistor: ~55 mA at Vf 3.1 V; 0.1 W. Adjust for the actual panel.')
q = dict(ref='Q1', lib='Transistor_FET:AO3400A', value='AO3400A', nets={'1': 'BL_PWM', '2': 'GND', '3': 'BL_K'},
         sch=[472, 82], xy=None, rot=0.0, side='back', dnp=False, fp='Package_TO_SOT_SMD:SOT-23',
         mpn='AO3400A', manufacturer='Alpha & Omega')
d['components'].append(q)
# Connectors: right-angle Dupont for battery PWM; unpopulated right-angle Dupont for external 5 V via D2.
C['J2'].update(fp='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical', mpn='HX PZ2.54-1x2P ZZ',
              manufacturer='hanxia')     # straight header: the enclosure has room above the back
j8 = copy.deepcopy(C['J2']); j8.update(ref='J8', value='5V EXT / Dupont (DNP)', nets={'1': 'GND', '2': 'EXT_5V'},
                                       sch=[393, 80], dnp=True, note='Unpopulated. External 5 V input through D2.')
d2 = dict(ref='D2', lib='Device:D_Schottky', value='B5819W', nets={'1': '+5V_SYS', '2': 'EXT_5V'}, sch=[420, 80],
          xy=None, rot=0.0, side='back', dnp=False, fp='Diode_SMD:D_SOD-123', mpn='B5819W SL',
          manufacturer='Changjiang', note='Blocks back-feed into an external 5 V source on J8.')
d['components'] += [j8, d2]
# E-paper: an external adapter (Good Display DESPI-C02 or any SPI e-paper module with its own driver board)
# supplies the panel's boost rails, so the on-board boost circuit and 24-pin FPC give way to an unfitted
# 1x8 2.54 mm SMD header (no through-hole pads under the TFT) in the DESPI-C02 pin order (1 BUSY ... 8 3.3V; a Waveshare module's cable is the reverse).
epd = ['J6', 'J7', 'R30', 'R31', 'R32', 'L3', 'Q3', 'D10', 'D11', 'D12', 'C30', 'C31', 'C32', 'C33', 'C34',
       'C35', 'C36', 'C38', 'C39', 'C40', 'C41']
d['components'] = [c for c in d['components'] if c['ref'] not in epd]
d['components'].append(dict(
    ref='J6', lib='Connector_Generic:Conn_01x08', value='E-PAPER ADAPTER (DNP)', sch=[430, 310], xy=None, rot=0.0,
    side='back', dnp=True, fp='Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical_SMD_Pin1Left',
    mpn='2.54mm 1x08 SMD pin header', manufacturer='',
    nets={'1': 'EPD_BUSY', '2': 'DISP_RST', '3': 'DISP_DC', '4': 'DISP_CS', '5': 'DISP_SCK', '6': 'DISP_MOSI',
          '7': 'GND', '8': '+3V2'},
    note='Unfitted. External e-paper adapter (DESPI-C02 order: BUSY, RES, D/C, CS, SCK, SDI, GND, 3.3V). '
         'Shares SPI, CS, DC and RESET with the TFT: fit one display.'))
# Cheaper equivalents.
C['U1'].update(value='ESP32-C3-MINI-1-H4X', mpn='ESP32-C3-MINI-1-H4X')
# 2-layer layout: display lines leave the module's top edge in the same order as the TFT connector J5
# (DC, CS, SCK, MOSI, RST), so the bus needs no crossings. DC IO10 (pin 16), CS IO4 (18), SCK IO5 (19).
C['U1']['nets'].update({'16': 'DISP_DC', '18': 'DISP_CS', '19': 'DISP_SCK'})
# USB-C: the same SHOU HAN TYPE-C 16P L6.5 as the battery board (J1/J7 there), with its drawing-checked
# footprint and catalogue 3D model. Its 13-land symbol merges A1/B12, A12/B1, A4/B9 and A9/B4.
d['custom_symbols'].append({'name': 'USB_C_SHOUHAN_16P', 'pins': [
    {'number': 'A1', 'name': 'GND_A1_B12', 'type': 'power_in', 'side': 'bottom'},
    {'number': 'A4', 'name': 'VBUS_A4_B9', 'type': 'passive', 'side': 'top'},
    {'number': 'A9', 'name': 'VBUS_A9_B4', 'type': 'passive', 'side': 'top'},
    {'number': 'A12', 'name': 'GND_A12_B1', 'type': 'power_in', 'side': 'bottom'},
    {'number': 'A5', 'name': 'CC1', 'type': 'passive', 'side': 'right'},
    {'number': 'B5', 'name': 'CC2', 'type': 'passive', 'side': 'right'},
    {'number': 'A6', 'name': 'D+_A', 'type': 'bidirectional', 'side': 'right'},
    {'number': 'B6', 'name': 'D+_B', 'type': 'bidirectional', 'side': 'right'},
    {'number': 'A7', 'name': 'D-_A', 'type': 'bidirectional', 'side': 'right'},
    {'number': 'B7', 'name': 'D-_B', 'type': 'bidirectional', 'side': 'right'},
    {'number': 'A8', 'name': 'SBU1', 'type': 'passive', 'side': 'right'},
    {'number': 'B8', 'name': 'SBU2', 'type': 'passive', 'side': 'right'},
    {'number': 'SH', 'name': 'SHIELD', 'type': 'passive', 'side': 'bottom'}]})
C['J1'].update(lib='AQI:USB_C_SHOUHAN_16P', fp='AQI:USB-C-SMD_TYPE-C-16P-L6.5', mpn='TYPE-C 16P L6.5',
               manufacturer='SHOU HAN', datasheet='../references/SHOUHAN-USB-C16-L6.5.pdf', side='back',
               nets={'A1': 'GND', 'A12': 'GND', 'SH': 'GND', 'A4': '+5V_SYS', 'A9': '+5V_SYS',
                     'A5': 'USB_CC1', 'B5': 'USB_CC2', 'A6': 'USB_D+', 'B6': 'USB_D+',
                     'A7': 'USB_D-', 'B7': 'USB_D-', 'A8': None, 'B8': None},
               note='Same connector as the battery board. Catalogue footprint corrected against the SHOU HAN '
                    'drawing (see integrated-power/review/CATALOG-REVIEW.md in devalopr/18650-USB-C-UPS); check mating/retention on the '
                    '1.6 mm board.')
for s in ('SW1', 'SW2', 'SW3'):
    C[s].update(fp='Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A', mpn='TS-1187A-B-A-B', manufacturer='XKB')
C['SW4'].update(value='POWER / MSK12C02', fp='Button_Switch_SMD:SW_SPDT_Shouhan_MSK12C02', mpn='MSK12C02',
                manufacturer='SHOU HAN')
C['J3'].update(mpn='XY-SM06B-GHS-TB', manufacturer='XYECO')
C['J4'].update(mpn='XY-SM04B-GHS-TB', manufacturer='XYECO')
C['D1'].update(manufacturer='TECH PUBLIC',
               # USBLC6 channels are identical; D- on I/O1 (1/6), D+ on I/O2 (3/4) lets the pair route uncrossed.
               nets={'1': 'USB_D-', '6': 'USB_D-', '3': 'USB_D+', '4': 'USB_D+', '2': 'GND', '5': '+5V_SYS'})
LCSC = {'U1': 'C41349510', 'U4': 'C2681320', 'U5': 'C479074', 'U6': 'C479074', 'Q1': 'C20917', 'D1': 'C2827654',
        'D2': 'C8598', 'L1': 'C83423', 'L2': 'C83423', 'J1': 'C49287211', 'J2': 'C32713268', 'J8': 'C32713268',
        'J3': 'C51940119', 'J4': 'C51940118', 'J5': 'C3168738', 'SW1': 'C318884', 'SW2': 'C318884',
        'SW3': 'C318884', 'SW4': 'C431540', 'U7': 'C2862740'}
BY_VALUE = {'10kR': 'C25804', '5.1kR': 'C23186', '22R': 'C23345', '100kR': 'C25803', '100R': 'C22775',
            '23.2kR': 'C49656146', '22kR': 'C31850', '4.7kR': 'C23162', '0R': 'C21189', '1kR': 'C21190',
            '33R': 'C25375', '1uF 16V': 'C15849', '100nF 25V': 'C14663', '1nF 25V': 'C1588',
            '10uF 25V': 'C15850', '22uF 10V': 'C45783', '100nF 16V': 'C1525'}
for c in d['components']:
    code = LCSC.get(c['ref']) or BY_VALUE.get(c['value'])
    if code:
        c['lcsc'] = code
# Only the SCD41 itself (hand-fitted later) and the J6/J8 headers stay unfitted; the CO2 supply (LDO U7 and its
# caps C15, C42, C16) is assembled so the sensor can be added without other parts.
for r in ('U7', 'C15', 'C16', 'C42'):
    C[r]['dnp'] = False
assert sorted(c['ref'] for c in d['components'] if c.get('dnp')) == ['J6', 'J8', 'U8']
d['cost_basis'] = {'date': '2026-09-27', 'source': 'PCBParts JLC/LCSC catalogue (pcbparts.dev), 1000-board tiers',
                   'inr_per_usd': 96}

d['notes'] = [
    {'text': 'AQI MAIN / REV B - ENGINEERING PROTOTYPE', 'x': 12, 'y': 10, 'size': 2.4},
    {'text': 'USB-C J1 is the only power/data input (standalone or from battery board J7). '
             'Battery % arrives as 100 Hz open-drain PWM on J2 (Dupont, 1=GND 2=BAT_PWM). '
             'Buttons: LEFT GPIO8, OK GPIO9 (BOOT), RIGHT GPIO2. J8 (DNP) = external 5 V via D2. TFT top contact confirmed by user. J6 (DNP) = external e-paper adapter, DESPI-C02 pin order; fit one display. One PM module.',
     'x': 12, 'y': 17}]
d['board_texts'][0]['text'] = 'AQI MAIN B'
d['telemetry'] = {'gpio': 21, 'connector': 'J2 1x02 2.54mm', 'pins': {'1': 'GND', '2': 'BAT_PWM'},
                  'pullup_ohms': 10000, 'series_ohms': 1000, 'frequency_hz': 100,
                  'high_duty_range': [0.1, 0.9], 'source': 'devalopr/18650-USB-C-UPS integrated-power J9'}
(out / 'design.json').write_text(json.dumps(d, indent=2) + '\n')
Project(out / 'design.json').schematic()
print('schematic regenerated:', len(d['components']), 'components')
