#!/usr/bin/env python3
"""Build native XFCE assets from the shipped sources and local brand artwork."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'.build/share'
# Stable install IDs keep existing selections and rollback journals working.
NAME = 'Fire-Walk-With-Me'
NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', 'http://www.w3.org/2000/svg')

def svg(body, size=64):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 64 64">{body}</svg>'

def background():
    return '''<defs><linearGradient id="velvet"><stop stop-color="#21040b"/>
    <stop offset=".36" stop-color="#8a1e36"/><stop offset=".6" stop-color="#5b1025"/>
    <stop offset="1" stop-color="#180309"/></linearGradient>
    <pattern id="folds" width="12" height="64" patternUnits="userSpaceOnUse"><rect width="12" height="64" fill="url(#velvet)"/></pattern></defs>
    <rect x="2" y="2" width="60" height="60" rx="8" fill="url(#folds)" stroke="#95616d" stroke-width=".6"/>'''

def brand_icon(source, target, palette=None, blossom=False):
    tree = ET.parse(source).getroot()
    if blossom:
        path = next(e.attrib['d'] for e in tree.iter() if e.tag==NS+'path')
        body = f'<g transform="scale(.08876560333)"><path fill="#fff" d="{path}"/></g>'
    else:
        text = ET.tostring(tree,encoding='unicode')
        for old,new in (palette or {}).items(): text=text.replace(old,new)
        tree=ET.fromstring(text)
        tree.set('width','64');tree.set('height','64');tree.set('viewBox','0 0 64 64')
        body='<g transform="translate(6 6) scale(.8125)">'+ET.tostring(tree,encoding='unicode')+'</g>'
    target.write_text(svg(background()+body))

def half_xpm(path):
    strings=re.findall(r'^"(.*)"(?:,|};)?$',path.read_text(),re.M)
    if not strings:return
    width,height,colors,cpp=map(int,strings[0].split())
    assert cpp==1,path
    assert width%2==0 and height%2==0,path
    rows=strings[colors+1:colors+1+height]
    assert len(rows)==height,path
    result=[f'{width//2} {height//2} {colors} 1',*strings[1:colors+1],
            *[row[::2] for row in rows[::2]]]
    path.write_text('/* XPM */\nstatic char * lodge[] = {\n'+',\n'.join('"'+x+'"' for x in result)+'\n};\n')

def build(fetch_chatgpt=False):
    if OUT.exists():shutil.rmtree(OUT)
    theme=OUT/'themes'/NAME;shutil.copytree(ROOT/'assets/theme',theme,symlinks=True)
    patterns={
      'chevron-rail.svg':'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="8"><path fill="#080708" d="M0 0h40v8H0z"/><path fill="#e6dece" d="M-10 0 0 5 10 0 20 5 30 0 40 5 50 0v3L40 8 30 3 20 8 10 3 0 8-10 3z"/></svg>',
      'panel-surface.svg':'<svg xmlns="http://www.w3.org/2000/svg" width="80" height="48"><defs><linearGradient id="v"><stop stop-color="#19080e"/><stop offset=".4" stop-color="#491425"/><stop offset=".7" stop-color="#2c0c19"/><stop offset="1" stop-color="#14060c"/></linearGradient><pattern id="fold" width="16" height="48" patternUnits="userSpaceOnUse"><rect width="16" height="48" fill="url(#v)"/></pattern><pattern id="chev" width="40" height="8" patternUnits="userSpaceOnUse"><path fill="#080708" d="M0 0h40v8H0z"/><path fill="#e6dece" d="M-10 0 0 5 10 0 20 5 30 0 40 5 50 0v3L40 8 30 3 20 8 10 3 0 8-10 3z"/></pattern></defs><rect width="80" height="48" fill="url(#fold)"/><rect width="80" height="8" fill="url(#chev)"/></svg>'}
    css=(ROOT/'assets/theme/gtk-3.0/fire-walk-with-me.css').read_text()
    for version in ['gtk-3.0','gtk-4.0']:
        for name,text in patterns.items():(theme/version/'assets'/name).write_text(text)
        (theme/version/'fire-walk-with-me.css').write_text(css)
        main=theme/version/'gtk.css';text=main.read_text()
        text=text.replace('@import url("black-lodge-details.css");','')
        for legacy in ['gtk-xfce4.css','gtk-xfce4-plugins.css','whisker-menu2.css']:
            text=text.replace(f'@import url("{legacy}");','')
        text=text.split('/* Black Lodge: legible ivory text')[0]
        main.write_text(text+'\n@import url("fire-walk-with-me.css");\n')
    # GTK4 removed legacy widget style properties. Keep its compatibility copy local.
    compat=theme/'gtk-4.0/compat';shutil.copytree(theme/'gtk-3.0',compat)
    for p in compat.rglob('*.css'):
        text=p.read_text()
        text=re.sub(r'\s*-(?:Gtk[\w-]*|treeview[\w-]*|gtk-outline-radius|gtk-icon-effect)\s*:[^;{}]+;', '',text)
        text=re.sub(r'([^{};\s])\s*}', r'\1;\n}',text)
        p.write_text(text.replace('*/;','*/'))
    p=theme/'gtk-4.0/gtk.css'
    p.write_text(p.read_text().replace('../gtk-3.0/gtk.css','compat/gtk.css'))
    p=theme/'gtk-4.0/settings.ini'
    p.write_text('\n'.join(line for line in p.read_text().splitlines() if not line.startswith(('gtk-auto-mnemonics','gtk-visible-focus','gtk-menu-images','gtk-button-images')))+'\n')
    # Keep HiDPI window assets; the ordinary variant is derived at half resolution.
    hidpi=OUT/'themes'/(NAME+'-HiDPI');(hidpi/'xfwm4').mkdir(parents=True)
    for p in (theme/'xfwm4').iterdir():shutil.copy2(p,hidpi/'xfwm4'/p.name)
    for directory in [theme/'xfwm4',hidpi/'xfwm4']:
        p=directory/'themerc';text=p.read_text()
        text=re.sub(r'^active_text_color=.*$', 'active_text_color=#B2CF94',text,flags=re.M)
        text+='\nactive_text_shadow_color=#38251e\ntitle_shadow_active=true\n'
        p.write_text(text)
    for p in (theme/'xfwm4').glob('*.xpm'):half_xpm(p)
    for directory,label in [(theme,'Firefox Walk With Me'),(hidpi,'Firefox Walk With Me HiDPI')]:
        (directory/'index.theme').write_text(f'[Desktop Entry]\nName={label}\nType=X-GNOME-Metatheme\n\n[X-GNOME-Metatheme]\nGtkTheme={NAME}\nIconTheme={NAME}\n')
        shutil.copy2(ROOT/'LICENSE',directory/'LICENSE')

    icons=OUT/'icons'/NAME;motifs=icons/'scalable/motifs'
    shutil.copytree(ROOT/'assets/icons/motifs',motifs)
    # The supplied Owl Cave geometry replaces the owl only on Start/distributor marks.
    symbol=ET.parse(ROOT/'assets/identity/owl-cave.svg').getroot()
    symbol.set('width','64');symbol.set('height','64');symbol.set('viewBox','0 -7 96 78')
    (motifs/'owl-cave.svg').write_text(ET.tostring(symbol,encoding='unicode'))
    payload=base64.b64encode((ROOT/'assets/identity/fox-lodge.png').read_bytes()).decode('ascii')
    fox=svg(f'<image width="64" height="64" href="data:image/png;base64,{payload}"/>')
    (motifs/'fox-lodge.svg').write_text(fox)
    aliases=json.loads((ROOT/'assets/icons/aliases.json').read_text())
    originals=aliases['apps']['owl'].split()
    starts=[x for x in originals if x in ['start-here','xfce4-whiskermenu','org.xfce.panel.whiskermenu','distributor-logo','distributor-logo-windows','mx-logo']]
    aliases['apps']['owl']=' '.join(x for x in originals if x not in starts)
    aliases['apps']['owl-cave']=' '.join(starts)+' fire-walk-with-me'
    aliases['apps']['fox-lodge']='firefox-walk-with-me'
    metadata=json.loads((ROOT/'assets/brand-sources.json').read_text())
    cache=ROOT/'.build/cache/chatgpt-logo.svg'
    if fetch_chatgpt and not cache.exists():
        source=metadata['chatgpt']
        with urllib.request.urlopen(source['bundle'],timeout=30) as response:data=response.read()
        content=zipfile.ZipFile(io.BytesIO(data)).read(source['member'])
        assert hashlib.sha256(content).hexdigest()==source['sha256'],'The official logo source changed; review it before using it.'
        cache.parent.mkdir(parents=True,exist_ok=True);cache.write_bytes(content)
    if cache.exists():
        assert hashlib.sha256(cache.read_bytes()).hexdigest()==metadata['chatgpt']['sha256']
        brand_icon(cache,motifs/'chatgpt.svg',blossom=True)
    else:aliases['apps'].pop('chatgpt',None)
    palettes={
      'firefox':{'#ffde3f':'#d0b779','#ff750e':'#be7441','#8357cd':'#574654','#ffba36':'#d1a36a','#f74e66':'#a34859'},
      'google-chrome':{'#109f5b':'#6f8555','#dd4d3e':'#9d4352','#ffce41':'#c7ad75','#4587f3':'#7493a5'}}
    brands={
      'firefox':['firefox','firefox-esr','org.mozilla.firefox'],
      'google-chrome':['google-chrome','google-chrome-stable'],
      'thunderbird':['thunderbird','org.mozilla.Thunderbird'],
      'vlc':['vlc'], 'libreoffice-writer':['libreoffice-writer'],
      'libreoffice-calc':['libreoffice-calc'], 'gimp':['gimp'], 'inkscape':['inkscape']}
    for brand,names in brands.items():
        for mapping in aliases.values():
            for key,values in list(mapping.items()):mapping[key]=' '.join(n for n in values.split() if n not in names)
        source=next((Path(base)/(brand+'.svg') for base in metadata['papirus']['local_roots'] if (Path(base)/(brand+'.svg')).exists()),None)
        if not source:continue
        brand_icon(source,motifs/(brand+'-lodge.svg'),palettes.get(brand,{}))
        aliases['apps'][brand+'-lodge']=' '.join(names)
    count=0
    for context,mapping in aliases.items():
        directory=icons/'scalable'/context;directory.mkdir()
        for motif,names in mapping.items():
            if not (motifs/(motif+'.svg')).exists():continue
            names=names.split();names += [n+'-open' for n in names if n.startswith('folder-')]
            for name in names:
                for suffix in ['', '-symbolic']:
                    path=directory/(name+suffix+'.svg');path.unlink(missing_ok=True)
                    path.symlink_to('../motifs/'+motif+'.svg');count+=1
    directories=['scalable/motifs',*['scalable/'+c for c in aliases]]
    index=f'[Icon Theme]\nName=Firefox Walk With Me\nComment=Velvet, chevrons, and recognizable application silhouettes\nInherits=Papirus-Dark,Adwaita,hicolor\nDirectories={",".join(directories)}\n'
    for directory in directories:
        context=directory.split('/')[1]
        context={'mimetypes':'MimeTypes'}.get(context,context.title())
        index+=f'\n[{directory}]\nSize=64\nMinSize=8\nMaxSize=512\nType=Scalable\nContext={context}\n'
    (icons/'index.theme').write_text(index)
    # Native cursors are built from SVG sources at logical and HiDPI sizes.
    cursor=OUT/'icons'/(NAME+'-Cursors');(cursor/'cursors').mkdir(parents=True)
    work=ROOT/'.build/cursor-frames';work.mkdir(exist_ok=True)
    hotspots={'left_ptr':(3,3),'hand2':(15,4)}
    alternate={'left_ptr':'default arrow top_left_arrow','xterm':'text ibeam','hand2':'pointer hand1 link','crosshair':'cross tcross','sb_h_double_arrow':'ew-resize h_double_arrow size_hor left_side right_side col-resize','sb_v_double_arrow':'ns-resize v_double_arrow size_ver top_side bottom_side row-resize','fleur':'move all-scroll size_all','bd_double_arrow':'nwse-resize size_fdiag top_left_corner bottom_right_corner','fd_double_arrow':'nesw-resize size_bdiag top_right_corner bottom_left_corner','not-allowed':'crossed_circle forbidden no-drop'}
    for source in (ROOT/'assets/cursors').glob('*.svg'):
        hx,hy=hotspots.get(source.stem,(16,16));spec=[]
        for size in [24,32,48,64]:
            image=work/f'{source.stem}-{size}.png'
            subprocess.run(['rsvg-convert','-w',str(size),'-h',str(size),str(source),'-o',str(image)],check=True)
            spec.append(f'{size} {round(hx*size/32)} {round(hy*size/32)} {image}\n')
        config=work/(source.stem+'.conf');config.write_text(''.join(spec))
        subprocess.run(['xcursorgen',str(config),str(cursor/'cursors'/source.stem)],check=True)
        for name in alternate[source.stem].split():(cursor/'cursors'/name).symlink_to(source.stem)
    (cursor/'index.theme').write_text('[Icon Theme]\nName=Firefox Walk With Me Cursors\nInherits=DMZ-White\n')
    data=OUT/'fire-walk-with-me';data.mkdir()
    shutil.copytree(ROOT/'assets/wallpapers',data/'wallpapers')
    shutil.copytree(ROOT/'assets/identity',data/'identity')
    shutil.copytree(ROOT/'runtime',data/'runtime')
    shutil.copytree(ROOT/'assets/audio',data/'audio')
    shutil.copy2(ROOT/'LICENSE',data/'LICENSE')
    for p in [theme/'gtk-3.0/assets/lodge-curtain.svg',theme/'gtk-3.0/assets/chevron-rail.svg']:
        shutil.copy2(p,data/'identity'/p.name)
    panel=theme/'gtk-3.0/assets/panel-surface.svg'
    for scale in [1,2]:
        target=data/'identity'/('panel-surface'+('-2x' if scale==2 else '')+'.png')
        subprocess.run(['rsvg-convert','-w',str(80*scale),'-h',str(44*scale),str(panel),'-o',str(target)],check=True)
    title=data/'identity/title.svg'
    mark=ET.fromstring(fox)
    mark.set('x','0');mark.set('y','0');mark.set('width','64');mark.set('height','64')
    title.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="385" height="64" viewBox="0 0 385 64">'+ET.tostring(mark,encoding='unicode')+'<text x="380" y="39" text-anchor="end" font-family="URW Gothic,DejaVu Sans,sans-serif" font-size="23" font-weight="bold" fill="#443126" stroke="#66bd60" stroke-width="1.5" paint-order="stroke fill">FIREFOX WALK WITH ME</text></svg>')
    subprocess.run(['rsvg-convert',str(title),'-o',str(title.with_suffix('.png'))],check=True)
    for p in OUT.rglob('*.svg'):ET.parse(p)
    assert all(p.exists() for p in OUT.rglob('*') if p.is_symlink())
    (ROOT/'.build/build.json').write_text(json.dumps({'theme':NAME,'icon_aliases':count,'chatgpt_composite':cache.exists(),'brand_sources':'local Papirus artwork; optional pinned official ChatGPT mark'},indent=2))
    print('Built native GTK/XFWM themes, icons, cursors, wallpaper, identity, and original audio.')
    return OUT

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fetch-chatgpt-logo',action='store_true')
    args=parser.parse_args();build(args.fetch_chatgpt_logo)
