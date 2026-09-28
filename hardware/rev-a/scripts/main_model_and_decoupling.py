"""Attach local models and add the LDO-side bypass for the remote CO2 island."""
from pathlib import Path
import pcbnew as p,json,copy
from kicad_common import uid
root=Path('hardware/rev-a/main');path=root/'AQI_Main.kicad_pcb';pro=root/'AQI_Main.kicad_pro';saved=pro.read_text();b=p.LoadBoard(str(path));F={f.GetReference():f for f in b.GetFootprints()}
for ref,file,z in [('U8','Sensirion_SCD4x.step',.829),('SW4','SW_SPDT_CK_JS102011SAQN.step',0)]:
 f=F[ref];models=f.Models();models.clear();model=p.FP_3DMODEL();model.m_Filename='${KIPRJMOD}/lib/3d/'+file;model.m_Offset.z=z;models.push_back(model)
d=json.loads((root/'design.json').read_text());D={c['ref']:c for c in d['components']}
if 'C42' not in F:
 c=copy.deepcopy(D['C15']);c.update(ref='C42',value='100nF 16V',nets={'1':'+3V3_CO2','2':'GND'},xy=[21,65],sch=[267,390],uuid=uid('AQI_MainC42'))
 d['components'].append(c)
 fp=p.FootprintLoad('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Capacitor_SMD.pretty','C_0603_1608Metric');fp.SetReference('C42');fp.SetValue(c['value']);fp.SetFPID(p.LIB_ID('Capacitor_SMD','C_0603_1608Metric'));fp.SetPosition(p.VECTOR2I(p.FromMM(21),p.FromMM(65)));fp.SetDNP(True)
 # Root UUID is unchanged; use an existing footprint's sheet path.
 parent=str(F['C15'].GetPath().AsString()).rsplit('/',1)[0];fp.SetPath(p.KIID_PATH(parent+'/'+c['uuid']))
 nets={n.GetNetname():n for n in b.GetNetsByName().values()}
 for pad in fp.Pads():pad.SetNet(nets[c['nets'][pad.GetNumber()]])
 b.Add(fp);fp.Flip(fp.GetPosition(),False);fp.Reference().SetLayer(p.B_Fab);fp.Value().SetVisible(False)
 placement=json.loads((root/'placement.json').read_text());placement['C42']={k:c[k] for k in ['xy','rot','side']};(root/'placement.json').write_text(json.dumps(placement,indent=2))
(root/'design.json').write_text(json.dumps(d,indent=2));p.SaveBoard(str(path),b);pro.write_text(saved)
