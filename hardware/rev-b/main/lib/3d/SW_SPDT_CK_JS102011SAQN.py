"""Simplified switch envelope aligned to KiCad's JS102011SAQN land pattern.
Body/actuator dimensions: C&K JS datasheet, right-angle SMT drawing.
https://www.ckswitches.com/media/1422/js.pdf
No internal mechanism. Cosmetic details and lead bends are simplified.
Model XY uses CAD coordinates (opposite PCB Y); Z=0 is the solder plane.
"""
from build123d import Box, Cylinder, Pos, Align, Compound, Color
BODY_X, BODY_Y, BODY_H = 9.0, 3.6, 3.5
ACTUATOR_X, ACTUATOR_PROJECTION = 1.5, 2.0

def gen_step():
    body=Pos(0,0,.15)*Box(BODY_X,BODY_Y,BODY_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body.label='Housing';body.color=Color(.12,.12,.12)
    actuator=Pos(-1.25,-2.8,1.4)*Box(ACTUATOR_X,ACTUATOR_PROJECTION,1.5)
    actuator.label='Actuator_position_A';actuator.color=Color(.06,.06,.06)
    children=[body,actuator]
    for i,x in enumerate([-2.5,0,2.5],1):
        lead=Pos(x,2.6,.15)*Box(.6,2.0,.3)
        lead.label=f'Terminal_{i}';lead.color=Color(.72,.72,.72);children.append(lead)
    for x in [-3.4,3.4]:
        peg=Pos(x,0,-.8)*Cylinder(.4,.95,align=(Align.CENTER,Align.CENTER,Align.MIN))
        peg.label='Locating_peg';peg.color=Color(.12,.12,.12);children.append(peg)
    return Compound(label='JS102011SAQN_simplified_envelope',children=children)
