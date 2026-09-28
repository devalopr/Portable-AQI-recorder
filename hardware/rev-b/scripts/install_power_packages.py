"""Install official-generator output and attach local models without changing lands.

Usage: python install_power_packages.py /path/to/generator-output
See integrated-power/lib/README.md for regeneration instructions.
"""
import sys
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1] / 'integrated-power/lib'
source = Path(sys.argv[1])
footprints = root / 'AQI_Power.pretty'
models = root / 'AQI_Power.3dshapes'
footprints.mkdir(exist_ok=True)
models.mkdir(exist_ok=True)
for p in (source / 'AQI_Power.pretty').glob('*.kicad_mod'):
    (footprints / p.name).write_text(p.read_text().replace(
        '${KICAD10_3DMODEL_DIR}/AQI_Power.3dshapes/',
        '${KIPRJMOD}/lib/AQI_Power.3dshapes/'))
for p in (source / 'AQI_Power.3dshapes').glob('*.step'):
    shutil.copy2(p, models / p.name)
standard = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Package_DFN_QFN.pretty/Texas_UQFN-10_1.5x2mm_P0.5mm.kicad_mod')
text = standard.read_text().replace(
    '${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/Texas_UQFN-10_1.5x2mm_P0.5mm.step',
    '${KIPRJMOD}/lib/AQI_Power.3dshapes/Texas_BQ24392_RSE_UQFN-10_1.5x2mm_P0.5mm.step')
(footprints / standard.name).write_text(text)
