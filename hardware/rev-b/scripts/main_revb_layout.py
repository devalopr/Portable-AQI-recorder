"""Rev B main PCB, stage 2: layout edits on top of the stage-1 netlist sync.

Rebuilds from the Rev A baseline every run: baseline -> main_revb_board.main() -> edits below.
Run with KiCad Python.
"""
import json, os, shutil, subprocess, sys
import pcbnew as pcb
from pathlib import Path
import main_revb_board as stage1
from pcb_edit import V, track, via, ripup, move, orient, orient_to, pads_of, free_via, place_header, prune, refill
from ground import swap_inner_routing, Stitcher

BASE = stage1.root / 'review/rev-a-baseline/AQI_Main.kicad_pcb'
USB = {'/USB_D+', '/USB_D-', '/USB_MCU_D+', '/USB_MCU_D-'}


def cleanup(b):
    """Remove copper that no longer matches the parts or positions (rerouted below)."""
    # All USB, CC and connector-side copper is rebuilt around the relocated USB-C.
    ripup(b, {'/USB_D+', '/USB_D-', '/USB_MCU_D+', '/USB_MCU_D-', '/USB_CC1', '/USB_CC2',
              '/BAT_PWM', '/BAT_PWM_MCU'})
    ripup(b, {'+5V_SYS'}, box=(17, 66, 44, 80))          # old J1 VBUS breakout / C4 / R12 loop
    ripup(b, {'GND'}, box=(17, 67.5, 44, 80))            # spokes to removed/moved pads
    # Stubs left by removed parts.
    ripup(b, {'/I2C_SDA'}, box=(16.5, 51.5, 17.2, 73), layers=('F',))
    ripup(b, {'+3V2'}, box=(17.5, 66, 25.0, 75), layers=('B',))
    ripup(b, {'+3V2'}, box=(25.0, 67.5, 28.1, 70.5), layers=('B', 'via'))
    ripup(b, {'GND'}, box=(34.5, 37.5, 39, 42.5), layers=('B',))
    ripup(b, {'+3V3_CO2'}, box=(19.95, 61.6, 21.2, 66), layers=('B',))
    ripup(b, {'+3V3_CO2'}, box=(19.3, 65.0, 19.7, 66.0), layers=('B',))
    ripup(b, {'GND'}, box=(17.5, 62.5, 19.6, 64.6), layers=('B',))
    # Buttons, strap nets, backlight, bucks and power switch are rerouted for the new parts.
    ripup(b, {'/BOOT_GPIO2', '/BOOT_GPIO8', '/BOOT_GPIO9', '/MCU_EN'}, box=(15.5, 20, 44, 70))
    ripup(b, {'/BOOT_GPIO2'})
    ripup(b, {'/BOOT_GPIO8'}, box=(12.5, 20, 40, 62.5))
    ripup(b, {'/CORE_SW', '/PM_SW', '/CORE_FB', '/PM_FB'})
    ripup(b, {'+5V_SW', 'GND', '+3V2'}, box=(3.0, 45.5, 13.5, 50.5), layers=('B',))
    ripup(b, {'+5V_SW', 'GND', '+3V3_PM'}, box=(1.0, 20.5, 11.5, 25.5), layers=('B',))
    ripup(b, {'/MAIN_ON', '+5V_SYS', 'GND'}, box=(37, 60, 44, 71), layers=('B', 'F'))

    # Former TPS2116 site: VBUS side (pins 3/5) and output side (pins 2/7) are one net now.
    track(b, '+5V_SYS', 'B', [(15.74, 56.84), (15.74, 57.34)], 0.3)
    track(b, '+5V_SYS', 'B', [(14.26, 56.84), (14.26, 57.84)], 0.3)
    # C42 up against U7 (output fed between its pins); C3 (100 nF) beside the ESP32 3V3 pin, C2 (10 uF)
    # in C3's old spot; GPIO8 strap pull-up next to the module.
    move(b, 'C42', 21.46, 64.25, 0)
    track(b, '+3V3_CO2', 'B', [(19.86, 61.14), (20.98, 62.25), (20.98, 64.25)], 0.3)
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    p2, p3 = fp['C2'].GetPosition(), fp['C3'].GetPosition()
    fp['C2'].SetPosition(p3); fp['C3'].SetPosition(p2)
    ripup(b, {'GND'}, box=(9.9, 59.6, 13.0, 62.6), layers=('B',))
    orient(b, 'R3', 11.6, 61.0, first_pad_up=True)
    track(b, '/BOOT_GPIO8', 'B', [(12.2, 62.75), (11.6, 62.15), (11.6, 61.8)])
    track(b, '+3V2', 'B', [(11.6, 60.2), (9.22, 60.2), (8.82, 60.0)], 0.3)


def bucks(b):
    """SY8089A1 (SOT-23-5) bucks. Pins sit in two rows: EN | GND | LX and FB | IN. EN takes +5V_SW and
    feeds IN through the channel under the body; GND drops into the In2 plane; LX runs to the inductor;
    FB leaves away from LX. Cin sits next to IN without courtyard overlap."""
    # ---- U5: +3V2 core rail ----
    lx_ne = {'3': (1, -1), '1': (-1, -1), '2': (0, -1), '5': (-1, 1), '4': (1, 1)}
    ripup(b, {'GND'}, box=(7.5, 51.0, 11.2, 57.2), layers=('B',))
    ripup(b, {'GND'}, box=(15.2, 52.6, 16.2, 55.0), layers=('B',))
    orient_to(b, 'U5', 11.8, 48.8, lx_ne)
    track(b, '/CORE_SW', 'B', [(12.75, 47.66), (15.0, 47.66)], 0.6)
    gx, gy = free_via(b, 'GND', 11.8, 46.75); track(b, 'GND', 'B', [(11.8, 47.66), (gx, gy)], 0.4)
    track(b, '+5V_SW', 'B', [(10.85, 47.66), (10.0, 47.49)], 0.4); via(b, '+5V_SW', 10.0, 47.49)
    track(b, '+5V_SW', 'B', [(10.85, 48.32), (10.85, 48.8), (12.75, 48.8), (12.75, 49.28)], 0.4)
    orient_to(b, 'C9', 12.3, 51.92, {'1': (1, 0), '2': (-1, 0)})
    track(b, '+5V_SW', 'B', [(12.75, 49.94), (13.25, 51.2)], 0.4)
    orient_to(b, 'R18', 8.2, 51.6, {'1': (-1, 0), '2': (1, 0)})
    orient_to(b, 'R17', 8.2, 53.3, {'1': (1, 0), '2': (-1, 0)})
    track(b, '/CORE_FB', 'B', [(10.85, 49.94), (10.4, 49.94), (7.38, 49.94), (7.38, 53.3)])
    track(b, 'GND', 'B', [(11.35, 51.92), (9.02, 51.6)], 0.4)
    gx, gy = free_via(b, 'GND', 10.2, 52.6); track(b, 'GND', 'B', [(11.35, 51.92), (gx, gy)], 0.4)
    track(b, '+3V2', 'B', [(9.02, 53.3), (9.02, 55.47), (8.82, 55.67)], 0.4)
    ripup(b, {'+3V2'}, box=(13.5, 47.5, 18.5, 52.6), layers=('B',))
    track(b, '+3V2', 'B', [(18.0, 48.0), (16.35, 46.35)], 0.6)
    track(b, '+3V2', 'B', [(18.0, 48.0), (18.3, 50.9), (17.45, 51.75), (17.45, 52.5)], 0.6)
    track(b, '+3V2', 'B', [(17.45, 52.5), (17.73, 52.78), (20.05, 52.78)], 0.6)
    track(b, '+3V2', 'B', [(17.45, 52.5), (17.45, 53.7), (12.7, 53.7), (11.99, 53.23)], 0.4)
    # ---- U6: +3V3_PM (SEN6x) rail (3-pin row north, IN south-east, Cin below) ----
    orient_to(b, 'U6', 10.4, 23.4, lx_ne)
    track(b, '/PM_SW', 'B', [(11.35, 22.26), (13.0, 22.26)], 0.6)
    v = free_via(b, 'GND', 10.4, 20.9, rmax=2.2, optional=True)
    if v: track(b, 'GND', 'B', [(10.4, 22.26), v], 0.4)
    track(b, '+5V_SW', 'B', [(9.45, 22.26), (3.0, 22.26), (2.56, 22.15)], 0.4)
    track(b, '+5V_SW', 'B', [(9.45, 22.26), (9.45, 23.4), (11.35, 23.4), (11.35, 24.54)], 0.4)
    orient_to(b, 'C12', 10.4, 26.55, {'1': (1, 0), '2': (-1, 0)})
    track(b, '+5V_SW', 'B', [(11.35, 24.54), (11.35, 26.55)], 0.4)
    gx, gy = free_via(b, 'GND', 9.45, 27.8); track(b, 'GND', 'B', [(9.45, 26.55), (gx, gy)], 0.4)
    orient_to(b, 'R19', 6.0, 26.5, {'1': (1, 0), '2': (-1, 0)})
    orient_to(b, 'R20', 6.0, 29.0, {'1': (-1, 0), '2': (1, 0)})
    ripup(b, {'+3V3_PM'}, box=(5.0, 25.5, 15.3, 26.6), layers=('B',))
    ripup(b, {'+3V3_PM'}, box=(11.5, 21.5, 12.1, 25.6), layers=('In1', 'In2', 'via'))
    ripup(b, {'GND'}, box=(4.5, 28.3, 6.0, 30.2), layers=('B',))
    track(b, '/PM_FB', 'B', [(9.45, 24.54), (6.0, 24.54), (5.17, 25.37), (5.17, 29.0)])
    track(b, '+3V3_PM', 'B', [(7.58, 25.74), (6.83, 26.5)], 0.4)
    track(b, '+3V3_PM', 'B', [(15.45, 25.74), (14.6, 25.74)], 0.6); via(b, '+3V3_PM', 14.6, 25.74)


def bottom(b):
    """SHOU HAN USB-C on the back at x=26.7 (mouth flush with the bottom edge), USBLC6 west of it, USB pair up the
    west side to ESP32 pins 26/27, CC/VBUS, Dupont headers J2/J8 at the bottom right, power switch SW4."""
    ripup(b, {'GND'}, box=(1.5, 66.0, 7.0, 70.0), layers=('F',))
    ripup(b, {'GND'}, box=(17.0, 62.0, 27.0, 67.5), layers=('F',))
    move(b, 'Q1', 36.5, 12.5)
    j1 = next(f for f in b.GetFootprints() if f.GetReference() == 'J1')
    if not j1.IsFlipped():
        j1.Flip(j1.GetPosition(), False)
    # Origin 4.09 mm inside the edge puts the mouth flush with it, as on the battery board.
    orient_to(b, 'J1', 26.7, 80.0 - 4.09, {'A5': (1, -1), 'B5': (-1, -1)})
    p = pads_of(b, 'J1'); P = p['A6'][1]                  # back pad row
    dp1, dp2, dm1, dm2 = p['B6'][0], p['A6'][0], p['A7'][0], p['B7'][0]
    # D+ joins above the pad row (over A7) and hops to the front; D- joins under the shell and runs west
    # between the rear and front shell slots (y 75.1 / 77.1).
    track(b, '/USB_D+', 'B', [(dp1, P), (dp1, P - 1.0), (dp2, P - 1.0), (dp2, P)])
    track(b, '/USB_D+', 'B', [(dm1, P - 1.0), (dm1, P - 1.9)]); via(b, '/USB_D+', dm1, P - 1.9)
    track(b, '/USB_D-', 'B', [(dm1, P), (dm1, P + 1.0), (dm2, P + 1.0), (dm2, P)])
    DY = 77.05                                            # D1 centre row: D- 76.1, VBUS/GND 77.05, D+ 78.0
    orient_to(b, 'D1', 19.2, DY, {'1': (1, -1), '3': (1, 1), '6': (-1, -1), '4': (-1, 1)})
    track(b, '/USB_D-', 'B', [(dm1, P + 1.0), (dm1, 75.4), (dm1 - 0.7, 76.1), (20.34, 76.1), (18.06, 76.1)])
    track(b, '/USB_D+', 'F', [(dm1, P - 1.9), (21.9, P - 1.9), (21.2, P - 1.2), (21.2, 78.0)])
    via(b, '/USB_D+', 21.2, 78.0)
    track(b, '/USB_D+', 'B', [(21.2, 78.0), (20.34, 78.0), (18.06, 78.0)])
    # CC pull-downs straight up from the pads; VBUS pads drop to the inner layer.
    cc1, cc2 = p['A5'][0], p['B5'][0]
    orient_to(b, 'R6', 23.6, 69.2, {'1': (1, 0), '2': (-1, 0)})
    orient_to(b, 'R5', 29.9, 69.2, {'1': (-1, 0), '2': (1, 0)})
    track(b, '/USB_CC2', 'B', [(cc2, P), (cc2, 70.0), (24.42, 69.45), (24.42, 69.2)])
    track(b, '/USB_CC1', 'B', [(cc1, P), (cc1, 70.0), (29.08, 69.45), (29.08, 69.2)])
    vw, ve = p['A9'][0], p['A4'][0]
    for x in (vw, ve):
        track(b, '+5V_SYS', 'B', [(x, P), (x, 70.9)], 0.5); via(b, '+5V_SYS', x, 70.9)
    track(b, '+5V_SYS', 'B', [(18.06, DY), (19.2, DY)], 0.3); via(b, '+5V_SYS', 19.2, DY)
    track(b, '+5V_SYS', 'In2', [(19.2, DY), (20.15, 76.1), (25.0, 76.1), (25.0, 71.4), (vw, 70.9)], 0.5)
    track(b, '+5V_SYS', 'In2', [(vw, 70.9), (39.0, 70.9)], 0.5)             # passes north of the D+ via
    via(b, '+5V_SYS', 39.0, 70.9)
    track(b, '+5V_SYS', 'In2', [(39.0, 70.9), (39.0, 62.1), (38.95, 61.56)], 0.5)
    # MCU side: D+ west, D- east going north; series resistors; turn west into pins 27 / 26.
    orient_to(b, 'R7', 16.9, 68.9, {'1': (0, 1), '2': (0, -1)})
    orient_to(b, 'R8', 18.1, 71.9, {'1': (0, 1), '2': (0, -1)})
    track(b, '/USB_D-', 'B', [(18.06, 76.1), (18.1, 75.8), (18.1, 72.7)])
    track(b, '/USB_MCU_D-', 'B', [(18.1, 71.1), (18.1, 65.3), (14.9, 65.3)])
    track(b, '/USB_D+', 'B', [(18.06, 78.0), (16.9, 78.0), (16.9, 69.7)])
    track(b, '/USB_MCU_D+', 'B', [(16.9, 68.1), (16.9, 66.1), (14.9, 66.1)])
    # Battery PWM: GPIO21 -> via -> inner layer north of VBUS -> via -> R34 / TP4 by J2; R33 pull-up.
    j2 = place_header(b, 'J2', 33.85, 75.35)             # pin 1 GND, pin 2 BAT_PWM
    j8 = place_header(b, 'J8', 39.95, 75.35)             # pin 1 GND, pin 2 EXT_5V
    xm = (j2['1'][0] + j2['2'][0]) / 2
    track(b, '/BAT_PWM_MCU', 'B', [(14.9, 69.3), (15.95, 69.3)]); via(b, '/BAT_PWM_MCU', 15.95, 69.3)
    track(b, '/BAT_PWM_MCU', 'In2', [(15.95, 69.3), (16.65, 70.0), (33.8, 70.0)])
    via(b, '/BAT_PWM_MCU', 33.8, 70.0)
    orient_to(b, 'R34', 37.15, 72.2, {'2': (-1, 0), '1': (1, 0)})
    track(b, '/BAT_PWM_MCU', 'B', [(33.8, 70.0), (33.8, 71.6), (34.4, 72.2), (36.325, 72.2)])
    move(b, 'TP4', 33.8, 71.2)
    track(b, '/BAT_PWM', 'B', [(37.975, 72.2), (37.975, 73.3), j2['2']])
    orient_to(b, 'R33', 37.15, 70.4, {'1': (-1, 0), '2': (1, 0)})
    track(b, '/BAT_PWM', 'B', [(37.975, 70.4), (37.975, 72.2)])
    track(b, '+3V2', 'B', [(30.82, 64.56), (30.82, 65.6), (34.6, 69.38), (35.8, 69.38), (36.325, 69.9),
                           (36.325, 70.4)], 0.3)
    move(b, 'TP6', 32.5, 67.28)
    # External 5 V (J8, unpopulated) through D2 into +5V_SYS.
    orient_to(b, 'D2', 41.2, 71.6, {'2': (1, 0), '1': (-1, 0)})
    d2 = pads_of(b, 'D2')
    track(b, '/EXT_5V', 'B', [j8['2'], (j8['2'][0], 73.5), (d2['2'][0], 72.6), d2['2']], 0.5)
    track(b, '+5V_SYS', 'B', [d2['1'], (39.0, 70.9)], 0.5)
    # Power switch: MSK12C02, actuator through the right edge (pads 1 +5V_SYS, 2 MAIN_ON, 3 GND).
    orient_to(b, 'SW4', 42.2, 65.2, {'1': (-1, -1), '3': (-1, 1)})
    sw = pads_of(b, 'SW4')
    track(b, '+5V_SYS', 'B', [(38.95, 61.56), (39.4, sw['1'][1]), sw['1']], 0.5)
    track(b, '/MAIN_ON', 'B', [(37.42, 64.34), (38.9, sw['2'][1]), sw['2']])


def buttons(b):
    """Front buttons on a 13 mm pitch, symmetric about the board centre: LEFT (x 9) -> GPIO8, OK (x 22) ->
    GPIO9 / BOOT, RIGHT (x 35) -> GPIO2."""
    for ref, x in [('SW1', 9.0), ('SW2', 22.0), ('SW3', 35.0)]:
        move(b, ref, x, 66.25)
    # LEFT / GPIO8: right-hand pad 1 drops onto the pin-22 escape via.
    track(b, '/BOOT_GPIO8', 'F', [(12.0, 64.375), (12.2, 63.9), (12.2, 62.75)])
    track(b, '/BOOT_GPIO8', 'F', [(6.0, 64.375), (6.8, 65.2), (11.2, 65.2), (12.0, 64.375)])
    # OK / GPIO9: the MAIN_QOD via under its right pad moves along its inner track; a spare GND via goes.
    ripup(b, {'/MAIN_QOD'}, box=(24.2, 64.2, 25.3, 65.3), layers=('B', 'In2', 'via'))
    track(b, '/MAIN_QOD', 'In2', [(19.31, 59.6), (19.31, 59.75), (23.4, 63.84), (23.85, 64.29), (23.85, 65.5)])
    # +5V_SW from U7 hugs x 23 so the via fits beside R16 pad 2.
    ripup(b, {'+5V_SW'}, box=(22.2, 63.0, 24.4, 66.6), layers=('B',))
    track(b, '+5V_SW', 'B', [(22.14, 63.04), (22.4, 63.04), (23.0, 63.64), (23.0, 66.1), (23.48, 66.58),
                             (24.82, 66.58)], 0.5)
    via(b, '/MAIN_QOD', 23.85, 65.5)
    track(b, '/MAIN_QOD', 'B', [(23.85, 65.5), (24.675, 65.5)])
    track(b, '/BOOT_GPIO9', 'F', [(19.0, 64.375), (20.0, 65.375), (20.0, 66.6), (24.7, 66.6), (24.7, 65.2),
                                  (25.0, 64.9), (25.0, 64.375)])
    track(b, '/BOOT_GPIO9', 'F', [(19.0, 64.375), (18.2, 63.55), (17.3, 63.5)]); via(b, '/BOOT_GPIO9', 17.3, 63.5)
    track(b, '/BOOT_GPIO9', 'In2', [(17.3, 63.5), (13.4, 63.5), (13.0, 64.45)])
    # RIGHT / GPIO2: pin-5 escape via, front run under the buttons, pull-up R4 behind SW3.
    track(b, '/BOOT_GPIO2', 'B', [(3.1, 69.3), (2.25, 69.25)]); via(b, '/BOOT_GPIO2', 2.25, 69.25)
    track(b, '/BOOT_GPIO2', 'F', [(2.25, 69.25), (2.9, 69.9), (22.5, 69.9), (23.5, 68.9), (29.6, 68.9), (30.95, 67.55),
                                  (30.95, 65.45), (32.0, 64.375)])
    track(b, '/BOOT_GPIO2', 'F', [(32.0, 64.375), (32.8, 63.55), (37.2, 63.55), (38.0, 64.375)])
    # MAIN_ON's via sat under SW3's right pad: drop it between the pads instead.
    ripup(b, {'/MAIN_ON'}, box=(37.0, 64.0, 37.8, 64.7))
    track(b, '/MAIN_ON', 'In2', [(35.2, 62.13), (36.6, 63.53), (36.6, 65.0)]); via(b, '/MAIN_ON', 36.6, 65.0)
    track(b, '/MAIN_ON', 'B', [(36.6, 65.0), (37.55, 65.95), (38.9, 65.95)])
    orient_to(b, 'R4', 32.0, 63.0, {'1': (-1, 0), '2': (1, 0)})
    track(b, '+3V2', 'B', [(31.175, 63.0), (30.82, 64.56)], 0.3)
    track(b, '/BOOT_GPIO2', 'B', [(32.825, 63.0), (33.6, 63.0)]); via(b, '/BOOT_GPIO2', 33.6, 63.0)
    track(b, '/BOOT_GPIO2', 'F', [(33.6, 63.0), (33.2, 63.55)])


def models(b):
    """Point the new switches at the local simplified STEP envelopes (not shipped in KiCad's library)."""
    local = {'SW_Push_1P1T_XKB_TS-1187A': 'SW_Push_1P1T_XKB_TS-1187A.step',
             'SW_SPDT_Shouhan_MSK12C02': 'SW_SPDT_Shouhan_MSK12C02.step'}
    for f in b.GetFootprints():
        name = str(f.GetFPID().GetLibItemName())
        if name in local:
            ms = f.Models()                  # index access: iterating the SWIG vector yields copies
            for i in range(len(ms)):
                ms[i].m_Filename = '${KIPRJMOD}/lib/3d/' + local[name]


def display(b):
    """Board-only DS1 carries the TFT panel model (42.72 x 60.26 x 2.5 mm) centred in the Rev A display envelope,
    with its flex wrapped over the top edge into J5; the envelope on Dwgs.User is labelled."""
    lib = str(Path(__file__).resolve().parents[1] / 'main/lib/AQI.pretty')
    f = pcb.FootprintLoad(lib, 'TFT_2.4in_ST7789_10P_Panel')
    f.SetPosition(V(22.0, 31.98)); f.SetReference('DS1')
    b.Add(f)
    for text, y in [('TFT DISPLAY BODY (FRONT)', 30.0), ('x 0.64-43.36, y 1.5-62.46', 32.5),
                    ('buttons below: SW1-3 bodies from y 63.7', 35.0)]:
        t = pcb.PCB_TEXT(b)
        t.SetText(text); t.SetLayer(pcb.Dwgs_User); t.SetPosition(V(22.0, y))
        t.SetTextSize(V(1.0, 1.0)); t.SetTextThickness(pcb.FromMM(0.15))
        b.Add(t)


def backlight(b):
    """AO3400A low-side switch where the STCS05A PWM/drain pins were; 33R 1206 series resistor at R28."""
    ripup(b, {'/BL_PWM'}, box=(36.9, 11.5, 39.2, 16.1), layers=('B',))
    try:
        orient_to(b, 'Q1', 38.0, 13.1, {'1': (-1, 1), '2': (-1, -1), '3': (1, 0)})
    except ValueError:
        orient_to(b, 'Q1', 38.0, 13.1, {'1': (-1, 1), '2': (-1, -1), '3': (1, 0)} if False else
                  {'3': (1, 0), '1': (-1, 1)})
    q = pads_of(b, 'Q1')
    track(b, '/BL_PWM', 'B', [(37.11, 16.16), (37.11, 14.6), q['1']])
    track(b, '/BL_K', 'B', [q['3'], (38.98, 14.4)], 0.3)
    v = free_via(b, 'GND', q['2'][0] - 0.9, q['2'][1], rmax=1.5)
    track(b, 'GND', 'B', [q['2'], v], 0.3)
    ripup(b, {'GND'}, box=(38.5, 16.0, 43.5, 21.0), layers=('B',))
    ripup(b, {'+5V_SW'}, box=(40.3, 12.0, 43.0, 17.6), layers=('B',))
    orient_to(b, 'R28', 40.6, 17.2, {'2': (0, -1), '1': (0, 1)})
    r = pads_of(b, 'R28')
    track(b, '/BL_A', 'B', [(39.71, 16.61), r['2']], 0.3)
    track(b, '+5V_SW', 'B', [(39.35, 18.98), r['1']], 0.6)


def edits(b):
    cleanup(b)
    bucks(b)
    bottom(b)
    buttons(b)
    backlight(b)
    models(b)
    display(b)
    ripup(b, {'+5V_SYS'}, box=(13.2, 58.7, 13.45, 59.0), layers=('B',))    # stub to removed R13
    ripup(b, {'+3V2'}, box=(37.4, 13.4, 37.9, 13.9), layers=('In2',))      # stubs to removed U10 EN
    ripup(b, {'+3V2'}, box=(39.5, 17.3, 40.0, 17.9), layers=('In2',))


# CO2 island stays thermally isolated: no stitching inside it (its pours join only at the bridge).
CO2_ISLAND = (27.0, 45.5, 44.0, 60.5)


def ground(b):
    moved = swap_inner_routing(b)
    refill(b)
    st = Stitcher(b, excl_boxes=[CO2_ISLAND])
    # 1) A via beside every decoupling/bulk capacitor and every IC/regulator ground pin.
    for f in b.GetFootprints():
        ref = f.GetReference()
        if ref[0] in 'CUDQJ' or ref.startswith('SW'):
            for pad in f.Pads():
                if pad.GetNetname() == 'GND' and pad.GetDrillSize().x == 0:
                    q = pad.GetPosition()
                    st.near(pcb.ToMM(q.x), pcb.ToMM(q.y))
    targeted = len(st.added)
    # 2) Dense stitching under the ESP32 ground area (outside the antenna keepout).
    under = st.grid(3.5, 63.4, 14.5, 73.6, 1.0)
    # 3) Board-edge fence and a general grid over open pour.
    edge = st.perimeter(44, 80, 0.9, 2.0)
    field = st.grid(1.5, 1.5, 42.5, 78.5, 3.0)
    print(f'ground: {moved} inner tracks moved to In1; stitching vias: {targeted} targeted, '
          f'{under} under ESP32, {edge} edge, {field} field')


def main():
    shutil.copy(BASE, stage1.board_path)
    subprocess.run([sys.executable, stage1.__file__], check=True, capture_output=True)
    b = pcb.LoadBoard(str(stage1.board_path))
    edits(b)
    n = prune(b)
    if not os.environ.get('NO_GROUND'):
        ground(b)
    refill(b)
    pcb.SaveBoard(str(stage1.board_path), b)
    sync_design(b)
    print('stage 2: pruned', n, 'dangling items')


def sync_design(b):
    """Record final board positions in design.json (same orientation convention as the board)."""
    path = stage1.root / 'design.json'
    d = json.loads(path.read_text())
    live = {f.GetReference(): f for f in b.GetFootprints()}
    for c in d['components']:
        f = live.get(c['ref'])
        if f is not None:
            c['xy'] = [round(pcb.ToMM(f.GetPosition().x), 4), round(pcb.ToMM(f.GetPosition().y), 4)]
            c['rot'] = round(f.GetOrientationDegrees(), 3)
            c['side'] = 'back' if f.IsFlipped() else 'front'
    d['copper_layers'] = 4
    path.write_text(json.dumps(d, indent=2) + '\n')


if __name__ == '__main__':
    main()
