from pathlib import Path
import zipfile
r=Path(__file__).resolve().parents[1];b=r/'battery';v=b/'review'
files=[r/'README.md',b/'design.json',b/'charge-policy.json',b/'fp-lib-table',b/'sym-lib-table']+list(b.glob('AQI_Battery_Compact.kicad_*'))+list((b/'lib').rglob('*'))
files += [v/n for n in ['AQI_Battery_Compact-fit-check.step','AQI_Battery_Compact.pdf','AQI_Battery_Compact.svg','compact-rear.png','compact-holder.png','schematic.png','copper-review.png','erc.json','drc.json','connectivity.json','validation.json','engineering-bom.csv','netlist.xml']]
with zipfile.ZipFile(r/'AQI-Battery-Compact-RevB-review.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files:
  if p.is_file():z.write(p,p.relative_to(r))
print('Updated review archive')
