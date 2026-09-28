"""Lumex drawing nominal 2.0 x 1.3 x 0.5mm body; footprint local X is long axis."""
from build123d import Box,Align

def gen_step():
 p=Box(2,1.3,.5,align=(Align.CENTER,Align.CENTER,Align.MIN));p.label='Lumex RGB body envelope';return p
