"""MAX17048 TDFN nominal 2 x 2 x 0.75mm body envelope."""
from build123d import Box,Align

def gen_step():
 p=Box(2,2,.75,align=(Align.CENTER,Align.CENTER,Align.MIN));p.label='MAX17048 body envelope';return p
