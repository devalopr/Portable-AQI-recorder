"""Shared deterministic KiCad 10 generation helpers for AQI boards.
Run with KiCad bundled Python; symbols are embedded, custom libraries local.
"""
import copy, json, math, re, uuid, os
from pathlib import Path
import pcbnew as pcb
K=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')
NS=uuid.UUID('567b173a-2b30-4248-96f0-5ffb47a4e9e1')
def uid(s): return str(uuid.uuid5(NS, s))
def q(s): return json.dumps(str(s), ensure_ascii=False)
def g(v): return round(round(v/1.27)*1.27, 4)
def eff(sz=1.27, extra=''): return f'(effects (font (size {sz} {sz})) {extra})'
def parse(s):
    ts = iter(re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]', s))
    def expr(t):
        if t != '(': return t
        a=[]
        for t in ts:
            if t == ')': return a
            a.append(expr(t))
    return expr(next(ts))
def ser(x): return '('+' '.join(ser(t) for t in x)+')' if isinstance(x,list) else x
def val(s): return json.loads(s) if s.startswith('"') else s
def children(x,k): return [t for t in x if isinstance(t,list) and t[0]==k]
def child(x,k): return next((t for t in x if isinstance(t,list) and t[0]==k),None)
libs={}
used={}
def symbol(libid):
    if libid in used: return used[libid]
    lib,name=libid.split(':')
    if lib not in libs:
        libs[lib]={val(t[1]):t for t in children(parse((K/'symbols'/f'{lib}.kicad_sym').read_text()),'symbol')}
    def resolve(n):
        raw=copy.deepcopy(libs[lib][n]); ext=child(raw,'extends')
        if ext:
            base=resolve(val(ext[1])); props={val(t[1]) for t in children(raw,'property')}
            base=[t for t in base if not(isinstance(t,list) and t[0]=='property' and val(t[1]) in props)]
            old=val(base[1]); base[1]=q(n)
            for t in children(base,'symbol'): t[1]=q(val(t[1]).replace(old+'_',n+'_',1))
            base.extend(t for t in raw[2:] if not(isinstance(t,list) and t[0]=='extends'))
            raw=base
        return raw
    s=resolve(name); s[1]=q(libid); used[libid]=s
    return s


def custom_symbol(spec):
    name=spec['name']; libid='AQI:'+name
    sides={side:[p for p in spec['pins'] if p.get('side','left')==side] for side in ['left','right','top','bottom']}
    h=max(len(sides['left']),len(sides['right']),3)*2.54/2+2.54
    w=max(10.16, max(len(sides['top']),len(sides['bottom']))*2.54/2+2.54)
    st=f'(symbol {q(libid)} (pin_names (offset 0.762)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 {h+5.08} 0) {eff()}) (property "Value" {q(name)} (at 0 {h+2.54} 0) {eff()}) (symbol {q(name+"_0_1")} (rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type background)))) (symbol {q(name+"_1_1")} '
    for side,ps in sides.items():
        for i,p in enumerate(ps):
            t=((len(ps)-1)/2-i)*2.54
            x,y,a={'left':(-w-2.54,t,0),'right':(w+2.54,t,180),'top':(t,h+2.54,270),'bottom':(t,-h-2.54,90)}[side]
            st+=f'(pin {p.get("type","passive")} line (at {x} {y} {a}) (length 2.54) (name {q(p["name"])} {eff(1.0)}) (number {q(p["number"])} {eff(1.0)}))'
    used[libid]=parse(st+'))')

class Project:
    def __init__(self,path):
        self.out=Path(path).parent; self.data=json.loads(Path(path).read_text()); self.name=self.data['name']
        self.root=uid(self.name); self.comps=self.data['components']
        for d in ['review','lib/AQI.pretty']: (self.out/d).mkdir(parents=True,exist_ok=True)
        for imp in self.data.get('import_symbols',[]):
            raw=parse((self.out/imp['path']).read_text())
            ss=copy.deepcopy(next(s for s in children(raw,'symbol') if val(s[1])==imp['name']))
            ss[1]=q(imp['libid']);used[imp['libid']]=ss
        for spec in self.data.get('custom_symbols',[]): custom_symbol(spec)
        for c in self.comps:
            c['uuid']=uid(self.name+'/'+c['ref']); c.setdefault('dnp',False);c.setdefault('rot',0)
            c['nets']={str(k):v for k,v in c['nets'].items()}
            s=symbol(c['lib']); prop=next((t for t in children(s,'property') if val(t[1])=='Footprint'),None)
            c.setdefault('fp',val(prop[2]) if prop else '')
            c.setdefault('mpn',c['value'] if c['ref'].startswith(('U','J','Q')) else '')
    def pins(self,c):
        return [p for un in children(symbol(c['lib']),'symbol') for p in children(un,'pin')]
    def schematic(self):
        ss=[]; power_index=0
        def wire(key,x,y,ex,ey):
            ss.append(f'(wire (pts (xy {x:.4f} {y:.4f}) (xy {ex:.4f} {ey:.4f})) (stroke (width 0) (type default)) (uuid {q(uid(self.name+key))}))')
        def label(key,n,x,y,just='left bottom'):
            ss.append(f'(label {q(n)} (at {x:.4f} {y:.4f} 0) {eff(1.27,"(justify "+just+")")} (uuid {q(uid(self.name+key))}))')
        for c in self.comps:
            s=symbol(c['lib']); x,y=map(g,c['sch']); pins=self.pins(c)
            body=f'(symbol (lib_id {q(c["lib"])}) (at {x} {y} 0) (unit 1) (in_bom {"no" if c["ref"].startswith("#") else "yes"}) (on_board yes) (dnp {"yes" if c["dnp"] else "no"}) (uuid {q(c["uuid"])}))'
            body=body[:-1]
            for name,v in [('Reference',c['ref']),('Value',c['value']),('Footprint',c['fp']),('MPN',c.get('mpn','')),('Manufacturer',c.get('manufacturer','')),('Datasheet',c.get('datasheet','')),('LCSC',c.get('lcsc','')),('Assembly note',c.get('note',''))]:
                prop=next((p for p in children(s,'property') if val(p[1])==name),None); a=child(prop,'at') if prop else None
                px,py=(x+float(a[1]),y-float(a[2])) if a else (x,y)
                justify=''
                if c['lib'].startswith('Device:') and name in ['Reference','Value']:
                    px=x+3.81;py=y+(-1.27 if name=='Reference' else 1.27);justify='(justify left)'
                hidden='(hide yes)' if name not in ['Reference','Value'] or c['ref'].startswith('#') else ''
                if name=='Value' and len(v)>24: v=v[:24] if c.get('short_value') else v
                body+=f'(property {q(name)} {q(v)} (at {px:.4f} {py:.4f} 0) {eff(1.0 if name=="Value" else 1.27,hidden+justify)})'
            connected=set()
            for p in pins:
                no=val(child(p,'number')[1]);body+=f'(pin {q(no)} (uuid {q(uid(c["uuid"]+"pin"+no))}))'
                a=child(p,'at');px=x+float(a[1]);py=y-float(a[2]);ang=float(a[3]);n=c['nets'].get(no)
                if n is None:
                    ss.append(f'(no_connect (at {px:.4f} {py:.4f}) (uuid {q(uid(c["uuid"]+"nc"+no))}))');continue
                if (px,py,n) in connected:continue
                connected.add((px,py,n))
                if no in c.get('direct_pins',{}):
                    pts=[(px,py)]+c['direct_pins'][no]
                    for j,(aa,zz) in enumerate(zip(pts,pts[1:])):
                        if abs(aa[0]-zz[0])+abs(aa[1]-zz[1])>1e-6:wire(c['ref']+'direct'+no+str(j),*aa,*zz)
                    continue
                dx=-5.08*math.cos(math.radians(ang));dy=5.08*math.sin(math.radians(ang));ex=px+dx;ey=py+dy
                wire(c['ref']+'wire'+no,px,py,ex,ey)
                # Visible conventional power symbols preserve obvious supply/ground direction.
                if (n=='GND' or n.startswith('+') or n in self.data.get('power_nets',[])) and abs(dx)<1e-6:
                    power_index+=1;pslib='power:GND' if n=='GND' else 'power:VDD'; ps=copy.deepcopy(symbol(pslib))
                    if n!='GND':
                        pl='AQI:'+re.sub(r'[^a-zA-Z0-9_]','_',n); ps[1]=q(pl)
                        for pr in children(ps,'property'):
                            if val(pr[1])=='Value':pr[2]=q(n)
                        for un in children(ps,'symbol'):
                            un[1]=q(val(un[1]).replace('VDD',pl.split(':')[1]))
                            for pp in children(un,'pin'):child(pp,'name')[1]=q(n if n.startswith('+') else '/'+n)
                        used[pl]=ps;pslib=pl
                    pref=f'#PWR{power_index:03d}'; puid=uid(c['uuid']+'power'+no)
                    # place supply above and ground below the wire endpoint, no rotation
                    gy=ey+(2.54 if n=='GND' else -2.54)
                    wire(pref,ex,ey,ex,gy)
                    ss.append(f'(symbol (lib_id {q(pslib)}) (at {ex:.4f} {gy:.4f} 0) (unit 1) (in_bom no) (on_board yes) (dnp no) (uuid {q(puid)}) (property "Reference" {q(pref)} (at {ex:.4f} {gy:.4f} 0) {eff(1.27,"(hide yes)")}) (property "Value" {q(n)} (at {ex:.4f} {gy+(3.81 if n=="GND" else -3.81):.4f} 0) {eff(1.0)}) (instances (project {q(self.name)} (path {q("/"+self.root)} (reference {q(pref)}) (unit 1)))))')
                else: label(c['ref']+'label'+no,n,ex,ey,'right bottom' if dx<-1e-6 else 'left bottom')
            body+=f'(instances (project {q(self.name)} (path {q("/"+self.root)} (reference {q(c["ref"])}) (unit 1)))))';ss.append(body)
        for i,b in enumerate(self.data.get('blocks',[])):
            x,y,w,h=[g(b[k]) for k in ['x','y','w','h']]
            ss.append(f'(rectangle (start {x} {y}) (end {x+w} {y+h}) (stroke (width 0.254) (type default) (color 75 100 120 1)) (fill (type none)) (uuid {q(uid(self.name+"block"+str(i)))}))')
            ss.append(f'(text {q(b["title"])} (at {x+3.81} {y+5.08} 0) (effects (font (size 1.8 1.8) (bold yes)) (justify left)) (uuid {q(uid(self.name+"title"+str(i)))}))')
        for i,n in enumerate(self.data.get('notes',[])):
            ss.append(f'(text {q(n["text"])} (at {g(n["x"])} {g(n["y"])} 0) {eff(n.get("size",1.27),"(justify left)")} (uuid {q(uid(self.name+"note"+str(i)))}))')
        out=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {q(self.root)}) (paper "A2") (title_block (title {q(self.name.replace("_"," "))}) (date "2026-09-07") (rev "A - ENGINEERING") (comment 1 "Verify release report before fabrication")) (lib_symbols '+''.join(ser(s) for s in used.values())+')'+''.join(ss)+'(sheet_instances (path "/" (page "1"))))'
        (self.out/f'{self.name}.kicad_sch').write_text(out)
        local=[]
        for k,s in used.items():
            if k.startswith('AQI:'):
                s=copy.deepcopy(s);s[1]=q(k.split(':')[1]);local.append(ser(s))
        (self.out/'lib/AQI.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '+''.join(local)+')')
        libs=sorted({c['lib'].split(':')[0] for c in self.comps}|{'power','AQI'})
        tab='(sym_lib_table (version 7)'
        for lib in libs:
            uri='${KIPRJMOD}/lib/AQI.kicad_sym' if lib=='AQI' else '${KICAD10_SYMBOL_DIR}/'+lib+'.kicad_sym'
            tab+=f'(lib (name {q(lib)}) (type "KiCad") (uri {q(uri)}) (options "") (descr ""))'
        (self.out/'sym-lib-table').write_text(tab+')')
    def board(self):
        mm=pcb.FromMM
        def vec(x,y):return pcb.VECTOR2I(mm(x),mm(y))
        b=pcb.BOARD();b.SetFileName(str(self.out/f'{self.name}.kicad_pcb'));b.SetCopperLayerCount(4)
        names={n for c in self.comps if c.get('xy') for n in c['nets'].values() if n};nets={}
        for i,n in enumerate(sorted(names),1):
            real=n if n=='GND' or n.startswith('+') else '/'+n
            nets[n]=pcb.NETINFO_ITEM(b,real,i);b.Add(nets[n])
        for c in self.comps:
            if not c.get('xy') or not c['fp']:continue
            lib,name=c['fp'].split(':');path=self.out/'lib/AQI.pretty' if lib=='AQI' else K/'footprints'/f'{lib}.pretty'
            f=pcb.FootprintLoad(str(path),name)
            if not f:raise ValueError('Missing footprint '+c['fp'])
            f.SetReference(c['ref']);f.SetValue(c['value']);f.SetFPID(pcb.LIB_ID(lib,name));f.SetPath(pcb.KIID_PATH('/'+self.root+'/'+c['uuid']))
            f.SetPosition(vec(*c['xy']));f.SetOrientationDegrees(c['rot']);f.SetDNP(c['dnp']);f.SetAttributes(f.GetAttributes() & ~pcb.FP_EXCLUDE_FROM_BOM)
            f.Reference().SetLayer(pcb.F_Fab);f.Reference().SetTextSize(vec(.7,.7));f.Reference().SetTextThickness(mm(.12));f.Value().SetVisible(False)
            pin_names={val(child(p,'number')[1]):val(child(p,'name')[1]) for p in self.pins(c)}
            for pad in f.Pads():
                no=pad.GetNumber();n=c['nets'].get(no)
                if n:pad.SetNet(nets[n])
                elif no in pin_names:
                    nn=f'unconnected-({c["ref"]}-{pin_names[no]}-Pad{no})';net=pcb.NETINFO_ITEM(b,nn,b.GetNetCount());b.Add(net);pad.SetNet(net)
            b.Add(f)
            if c.get('side')=='back':f.Flip(f.GetPosition(),False);f.Reference().SetLayer(pcb.B_Fab)
        w,h=self.data['width'],self.data['height'];ch=1.5
        outline=[(ch,0),(w-ch,0),(w,ch),(w,h-ch),(w-ch,h),(ch,h),(0,h-ch),(0,ch)]
        for a,z in zip(outline,outline[1:]+outline[:1]):
            sh=pcb.PCB_SHAPE();sh.SetShape(pcb.SHAPE_T_SEGMENT);sh.SetStart(vec(*a));sh.SetEnd(vec(*z));sh.SetLayer(pcb.Edge_Cuts);sh.SetWidth(mm(.05));b.Add(sh)
        for t in self.data.get('board_texts',[]):
            tt=pcb.PCB_TEXT(b);tt.SetText(t['text']);tt.SetPosition(vec(*t['xy']));tt.SetTextSize(vec(t.get('size',.8),t.get('size',.8)));tt.SetTextThickness(mm(.12));ly=getattr(pcb,t.get('layer','F_SilkS'));tt.SetLayer(ly);tt.SetMirrored(ly==pcb.B_SilkS);b.Add(tt)
        for area in self.data.get('keepouts',[]):
            for layer in [pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu]:
                z=pcb.ZONE(b);z.SetLayer(layer);z.SetIsRuleArea(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(True);z.SetDoNotAllowFootprints(False)
                poly=z.Outline();poly.NewOutline()
                for x,y in area:poly.Append(mm(x),mm(y))
                b.Add(z)
        # Document display/body envelopes separately from electrical keepouts.
        for e in self.data.get('envelopes',[]):
            sh=pcb.PCB_SHAPE();sh.SetShape(pcb.SHAPE_T_RECT);sh.SetStart(vec(*e['start']));sh.SetEnd(vec(*e['end']));sh.SetLayer(pcb.Dwgs_User);sh.SetWidth(mm(.15));b.Add(sh)
        pcb.SaveBoard(str(self.out/f'{self.name}.kicad_pcb'),b)
        tab='(fp_lib_table (version 7)'
        for lib in sorted({c['fp'].split(':')[0] for c in self.comps if c.get('xy') and c['fp']}):
            uri='${KIPRJMOD}/lib/AQI.pretty' if lib=='AQI' else '${KICAD10_FOOTPRINT_DIR}/'+lib+'.pretty'
            tab+=f'(lib (name {q(lib)}) (type "KiCad") (uri {q(uri)}) (options "") (descr ""))'
        (self.out/'fp-lib-table').write_text(tab+')')
    def settings(self):
        classes=[]
        for name,width,clear,col in [('Default',.2,.15,'rgba(0,0,0,0)'),('Power',.6,.15,'rgba(190,60,30,1)'),('USB',.2,.15,'rgba(120,50,180,1)'),('I2C',.2,.15,'rgba(25,115,160,1)'),('SPI',.2,.15,'rgba(25,135,90,1)')]:
            classes.append(dict(name=name,clearance=clear,track_width=width,via_diameter=.6,via_drill=.3,uvia_diameter=.3,uvia_drill=.1,diff_pair_width=.2,diff_pair_gap=.15,diff_pair_via_gap=.25,pcb_color='rgba(0,0,0,0)',schematic_color=col,wire_width=6,bus_width=12,line_style=0))
        patterns=[{'netclass':cl,'pattern':pat} for cl,pat in [('Power','+*'),('USB','/USB*'),('I2C','/*SDA*'),('I2C','/*SCL*'),('SPI','/DISP*')]]
        data={'meta':{'filename':self.name+'.kicad_pro','version':3},'net_settings':{'classes':classes,'netclass_patterns':patterns,'meta':{'version':3}},'board':{'design_settings':{'rules':{'min_clearance':.15,'min_track_width':.15,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_hole_clearance':.25,'min_copper_edge_clearance':.3},'meta':{'version':2}}}}
        (self.out/f'{self.name}.kicad_pro').write_text(json.dumps(data,indent=2))
    def build(self):self.schematic();self.board();self.settings();print(self.name,len(self.comps),'components')

if __name__=='__main__':
    import sys
    Project(sys.argv[1]).build()
