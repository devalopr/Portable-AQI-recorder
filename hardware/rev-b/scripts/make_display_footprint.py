"""Write AQI:TFT_2.4in_ST7789_10P_Panel, a board-only (no pads, not in BOM/CPL) footprint that carries the
TFT panel 3D model and its outline. Origin = panel centre. Run with KiCad's Python."""
from pathlib import Path
import pcbnew as pcb

LIB = Path(__file__).resolve().parents[1] / 'main/lib/AQI.pretty'
W, H = 42.72, 60.26
AA_W, AA_H, AA_FPC = 36.72, 48.96, 8.1


def V(x, y):
    return pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))


def rect(fp, x0, y0, x1, y1, layer, w):
    s = pcb.PCB_SHAPE(fp, pcb.SHAPE_T_RECT)
    s.SetStart(V(x0, y0)); s.SetEnd(V(x1, y1)); s.SetLayer(layer); s.SetWidth(pcb.FromMM(w))
    fp.Add(s)


def main():
    b = pcb.BOARD()
    fp = pcb.FOOTPRINT(b)
    fp.SetFPID(pcb.LIB_ID('AQI', 'TFT_2.4in_ST7789_10P_Panel'))
    fp.SetLibDescription('2.4" 240x320 ST7789 TFT panel, 42.72 x 60.26 x 2.5 mm, 10-way 1.0 mm FPC wrapped to J5. '
                         'Mechanical only: carries the 3D model and outline.')
    fp.SetKeywords('TFT ST7789 display panel mechanical')
    fp.SetReference('DS1'); fp.SetValue('TFT 2.4in ST7789 (panel)')
    for field, y in ((fp.Reference(), -2.0), (fp.Value(), 2.0)):
        field.SetLayer(pcb.F_Fab); field.SetPosition(V(0, y)); field.SetVisible(True)
    fp.SetBoardOnly(True); fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True)
    fp.SetAttributes(pcb.FP_EXCLUDE_FROM_BOM | pcb.FP_EXCLUDE_FROM_POS_FILES | pcb.FP_BOARD_ONLY)
    rect(fp, -W / 2, -H / 2, W / 2, H / 2, pcb.F_Fab, 0.1)
    top = -H / 2                                    # FPC end, toward the board's top edge
    rect(fp, -AA_W / 2, top + AA_FPC, AA_W / 2, top + AA_FPC + AA_H, pcb.F_Fab, 0.1)
    rect(fp, -W / 2 - 0.25, -H / 2 - 0.25, W / 2 + 0.25, H / 2 + 0.25, pcb.F_CrtYd, 0.05)
    m = pcb.FP_3DMODEL()
    m.m_Filename = '${KIPRJMOD}/lib/3d/TFT_2.4in_ST7789_10P_Panel.step'
    fp.Add3DModel(m)
    pcb.FootprintSave(str(LIB), fp)
    print('wrote', LIB / 'TFT_2.4in_ST7789_10P_Panel.kicad_mod')


if __name__ == '__main__':
    main()
