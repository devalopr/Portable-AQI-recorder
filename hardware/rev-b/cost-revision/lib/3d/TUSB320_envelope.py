"""TI RWB nominal 1.6 x 1.6 x 0.4mm body envelope; not lead-detail CAD."""
from build123d import Box,Align

def gen_step():
 p=Box(1.6,1.6,.4,align=(Align.CENTER,Align.CENTER,Align.MIN));p.label='TUSB320 RWB body envelope';return p
