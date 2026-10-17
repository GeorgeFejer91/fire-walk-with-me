#!/usr/bin/env python3
"""Install native assets and narrowly scoped preferences, with private rollback."""
import argparse
import configparser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NAME = 'Fire-Walk-With-Me'

def remove(path):
    if path.is_symlink() or path.is_file(): path.unlink()
    elif path.is_dir(): shutil.rmtree(path)

class Changes:
    def __init__(self, state):
        self.state = state
        state.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.journal = state/'rollback.json'
        self.records = json.loads(self.journal.read_text()) if self.journal.exists() else {'files':{}, 'xfconf':{}}

    def save(self):
        temp = self.state/'rollback.tmp'
        temp.write_text(json.dumps(self.records, indent=2)+'\n'); temp.chmod(0o600)
        temp.replace(self.journal)

    def backup(self, path):
        key = str(path)
        if key in self.records['files']: return
        backup = self.state/('file-'+uuid.uuid4().hex)
        present = path.exists() or path.is_symlink()
        if present:
            if path.is_symlink(): backup.symlink_to(os.readlink(path))
            elif path.is_dir(): shutil.copytree(path, backup, symlinks=True)
            else: shutil.copy2(path, backup)
        self.records['files'][key] = str(backup) if present else None
        self.save()

    def text(self, path, content):
        self.backup(path); path.parent.mkdir(parents=True, exist_ok=True)
        # Replace rather than following an existing symlink into unrelated data.
        remove(path); path.write_text(content)

    def copy(self, source, destination):
        self.backup(destination); destination.parent.mkdir(parents=True, exist_ok=True)
        remove(destination)
        if source.is_dir(): shutil.copytree(source, destination, symlinks=True)
        else: shutil.copy2(source, destination)

    def link(self, path, target):
        self.backup(path); path.parent.mkdir(parents=True, exist_ok=True)
        remove(path); path.symlink_to(target)

    def restore_files(self):
        for destination, backup in reversed(list(self.records['files'].items())):
            path = Path(destination); remove(path)
            if backup:
                source = Path(backup)
                if source.is_symlink(): path.symlink_to(os.readlink(source))
                elif source.is_dir(): shutil.copytree(source, path, symlinks=True)
                else: shutil.copy2(source, path)

def xml_settings(path, channel, values):
    root = ET.parse(path).getroot() if path.exists() else ET.Element('channel', name=channel, version='1.0')
    for key, value in values.items():
        node = root
        parts = key.strip('/').split('/')
        for part in parts:
            child = next((c for c in node.findall('property') if c.get('name')==part),None)
            if child is None: child = ET.SubElement(node, 'property', name=part, type='empty')
            node = child
        for child in node.findall('value'): node.remove(child)
        if isinstance(value,list):
            node.set('type','array'); node.attrib.pop('value',None)
            for item in value:
                ET.SubElement(node,'value',type='int' if isinstance(item,int) else 'string',value=str(item))
        else:
            kind = 'bool' if isinstance(value,bool) else 'int' if isinstance(value,int) else 'string'
            node.set('type',kind); node.set('value',str(value).lower() if isinstance(value,bool) else str(value))
    ET.indent(root)
    return '<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode')+'\n'

def desktop(name, command, comment=''):
    return f'[Desktop Entry]\nType=Application\nName={name}\nComment={comment}\nExec={command}\nOnlyShowIn=XFCE;\nNoDisplay=true\nX-GNOME-Autostart-enabled=true\n'

def channel_defaults(data):
    return {
      'xsettings': {'/Net/ThemeName':NAME,'/Net/IconThemeName':NAME,
                    '/Gtk/CursorThemeName':NAME+'-Cursors'},
      'xfwm4': {'/general/theme':NAME, '/general/title_font':'URW Gothic Bold 10'},
      'xfce4-desktop': {},
      'xfce4-terminal': {'/'+re.sub(r'(?<!^)(?=[A-Z])','-',key).lower(): (value=='TRUE' if value in ['TRUE','FALSE'] else value) for key,value in terminal_values().items()},
    }

def panel_defaults(data):
    return {'/configver':2, '/panels':[1], '/panels/panel-1/position':'p=10;x=0;y=0',
      '/panels/panel-1/position-locked':True,'/panels/panel-1/length':100,
      '/panels/panel-1/mode':0,'/panels/panel-1/nrows':1,'/panels/panel-1/size':44,
      '/panels/panel-1/icon-size':24,
      '/panels/panel-1/background-style':2,
      '/panels/panel-1/background-image':str(data/'identity/panel-surface.png'),
      '/panels/panel-1/plugin-ids':[20,2,15,5,6,7,1,9],
      '/plugins/plugin-20':'whiskermenu','/plugins/plugin-20/button-icon':'fire-walk-with-me',
      '/plugins/plugin-20/button-title':'Lodge','/plugins/plugin-20/show-button-title':True,
      '/plugins/plugin-20/show-button-icon':True,'/plugins/plugin-20/menu-width':470,
      '/plugins/plugin-20/menu-height':550,'/plugins/plugin-20/position-search-alternate':True,
      '/plugins/plugin-20/favorites':['firefox.desktop','thunar.desktop','xfce4-terminal.desktop'],
      '/plugins/plugin-2':'docklike','/plugins/plugin-15':'separator',
      '/plugins/plugin-15/expand':True,'/plugins/plugin-15/style':0,
      '/plugins/plugin-5':'pulseaudio','/plugins/plugin-6':'systray',
      '/plugins/plugin-6/single-row':True,'/plugins/plugin-6/icon-size':24,
      '/plugins/plugin-7':'power-manager-plugin','/plugins/plugin-1':'clock',
      '/plugins/plugin-1/digital-layout':3,'/plugins/plugin-1/digital-time-format':'%H:%M',
      '/plugins/plugin-1/digital-time-font':'URW Gothic Bold 10',
      '/plugins/plugin-9':'actions','/plugins/plugin-9/appearance':0,
      '/plugins/plugin-9/items':['+logout']}

def patch_ini(path, section, values):
    cfg = configparser.ConfigParser(interpolation=None,strict=False)
    cfg.optionxform = str
    if path.exists():cfg.read(path)
    if not cfg.has_section(section):cfg.add_section(section)
    for key,value in values.items():cfg[section][key]=value
    import io
    text=io.StringIO();cfg.write(text,space_around_delimiters=False)
    return text.getvalue()

def terminal_values():
    return {
      'ColorForeground':'#b2cf94','ColorBackground':'#0d090d','ColorCursor':'#d5c8a8',
      'ColorPalette':'#100c10;#ad5367;#99b67a;#c6ae75;#7694a6;#a67f9d;#80a6a0;#e5d9c2;#75636c;#d8818d;#bdd7a0;#e7cf91;#9db6c5;#c4a4ba;#a9cbc2;#fff0d7',
      'FontName':'Liberation Mono 11','BackgroundMode':'TERMINAL_BACKGROUND_SOLID',
      'MiscCursorShape':'TERMINAL_CURSOR_SHAPE_BLOCK','MiscBell':'FALSE',
      'ColorUseTheme':'FALSE','ColorSelection':'#812c37'}

def terminal(path):
    return patch_ini(path,'Configuration',terminal_values())

def launchers(changes, directory):
    for filename,name in [('thunar.desktop','Black Lodge'),('xfce4-terminal.desktop','Red Room Terminal')]:
        path=directory/filename
        source=path if path.exists() else Path('/usr/share/applications')/filename
        if not source.exists():continue
        cfg=configparser.ConfigParser(interpolation=None,strict=False);cfg.optionxform=str;cfg.read(source)
        for key in list(cfg['Desktop Entry']):
            if key=='Name' or key.startswith('Name['):cfg['Desktop Entry'][key]=name
        cfg['Desktop Entry']['Icon']='org.xfce.thunar' if filename=='thunar.desktop' else 'utilities-terminal'
        import io
        out=io.StringIO();cfg.write(out,space_around_delimiters=False);changes.text(path,out.getvalue())

def setup_files(changes, config, data, startup):
    changes.text(config/'autostart/black-lodge-titles.desktop', desktop('Black Lodge Window Names',f'/usr/bin/python3 "{data}/runtime/session.py"'))
    if shutil.which('conky'):
        changes.text(config/'conky/Fire-Walk-With-Me.conf',(ROOT/'profiles/conky.conf').read_text().replace('@DATA@',str(data)))
        changes.text(config/'autostart/conky.desktop',desktop('Firefox Walk With Me Clock',f'conky -c "{config}/conky/Fire-Walk-With-Me.conf"'))
    if startup:
        changes.text(config/'autostart/fire-walk-with-me-sound.desktop',desktop('Into the Lodge',f'paplay --volume=36000 "{data}/audio/into-the-lodge.wav"','Original synthesized desktop-login cue'))
    path=config/'xfce4/terminal/terminalrc';changes.text(path,terminal(path))
    for version in ['gtk-3.0','gtk-4.0']:
        path=config/version/'settings.ini'
        changes.text(path,patch_ini(path,'Settings',{'gtk-theme-name':NAME,'gtk-icon-theme-name':NAME,'gtk-cursor-theme-name':NAME+'-Cursors'}))

def xfconf():
    import dbus
    return dbus.Interface(dbus.SessionBus().get_object('org.xfce.Xfconf','/org/xfce/Xfconf'),'org.xfce.Xfconf')

def encode(value):
    import dbus
    if isinstance(value,dbus.Array):return {'type':'Array','signature':str(value.signature),'value':[encode(x) for x in value]}
    kind=type(value).__name__
    return {'type':kind,'value':bool(value) if kind=='Boolean' else float(value) if kind=='Double' else int(value) if kind in ['Int32','UInt32','Int64','UInt64'] else str(value)}

def decode(item):
    import dbus
    if item['type']=='Array':return dbus.Array([decode(x) for x in item['value']],signature=item['signature'])
    return getattr(dbus,item['type'])(item['value'])

def live_settings(changes, channels):
    import dbus
    service=xfconf()
    for channel,values in channels.items():
        existing=service.GetAllProperties(channel,'/')
        for key,value in values.items():
            record=changes.records['xfconf'].setdefault(channel,{})
            if key not in record:
                record[key]=encode(existing[key]) if key in existing else None;changes.save()
            old=existing.get(key)
            if old is not None:
                if isinstance(old,dbus.Array):new=dbus.Array(value,signature='v')
                else:new=type(old)(value)
            elif isinstance(value,bool):new=dbus.Boolean(value)
            elif isinstance(value,int):new=dbus.Int32(value)
            elif isinstance(value,list):new=dbus.Array(value,signature='v')
            else:new=dbus.String(value)
            service.SetProperty(channel,key,new)

def stop_previous_helpers():
    # Stop only this user's known title helper and themed clock, never other Conky instances.
    import signal
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:
            if proc.stat().st_uid!=os.getuid():continue
            args=(proc/'cmdline').read_bytes().split(b'\0')
            title=any(x.endswith(b'/black-lodge-titles') or x.endswith(b'/runtime/window-names.py') for x in args)
            clock=args[0].endswith(b'conky') and any(x.endswith((b'/Black-Lodge.conf',b'/Fire-Walk-With-Me.conf')) for x in args)
            if title or clock:os.kill(int(proc.name),signal.SIGTERM)
        except (FileNotFoundError,PermissionError,ProcessLookupError):pass

def apply_user(changes, share, startup):
    data=share/'fire-walk-with-me';config=Path.home()/'.config'
    if not data.exists():raise SystemExit('Install the assets first.')
    stop_previous_helpers()
    setup_files(changes,config,data,startup)
    launchers(changes,Path.home()/'.local/share/applications')
    changes.link(Path.home()/'.icons'/(NAME+'-Cursors'),share/'icons'/(NAME+'-Cursors'))
    changes.text(Path.home()/'.icons/default/index.theme','[Icon Theme]\nName=Default\nInherits='+NAME+'-Cursors\n')
    channels=channel_defaults(data);service=xfconf()
    xsettings=service.GetAllProperties('xsettings','/')
    if int(xsettings.get('/Gdk/WindowScalingFactor',1))>=2:channels['xfwm4']['/general/theme']=NAME+'-HiDPI'
    desktop_properties=service.GetAllProperties('xfce4-desktop','/')
    for key in desktop_properties:
        if key.endswith('/last-image'):channels['xfce4-desktop'][key]=str(data/'wallpapers/red-room.png')
        if key.endswith('/image-style'):channels['xfce4-desktop'][key]=5
    panel=service.GetAllProperties('xfce4-panel','/')
    values={}
    for key,value in panel.items():
        if key.endswith('/background-style'):
            values[key]=2
            values[key.rsplit('/',1)[0]+'/icon-size']=24
            suffix='-2x' if int(xsettings.get('/Gdk/WindowScalingFactor',1))>=2 else ''
            values[key.rsplit('/',1)[0]+'/background-image']=str(data/'identity'/('panel-surface'+suffix+'.png'))
        if key.endswith('/size') and key.startswith('/panels/'):values[key]=44
        if key.endswith('/button-icon') and 'plugin-' in key:values[key]='fire-walk-with-me'
        if key.endswith('/digital-time-font'):values[key]='URW Gothic Bold 10'
        if key.endswith('/icon-size') and panel.get(key.rsplit('/',1)[0])=='systray':values[key]=24
        if key.endswith('/size-max') and panel.get(key.rsplit('/',1)[0])=='systray':values[key]=24
        if value=='systray' and key.startswith('/plugins/plugin-'):values[key+'/single-row']=True
    channels['xfce4-panel']=values
    live_settings(changes,channels)
    changes.text(changes.state/'wallpaper-initialized','Applied desktop wallpaper.\n')
    # Existing GTK4 app-specific theme choices may take precedence over the desktop theme.
    for version in ['gtk-3.0','gtk-4.0']:
        path=config/version/'settings.ini'
        changes.text(path,patch_ini(path,'Settings',{'gtk-theme-name':NAME,'gtk-icon-theme-name':NAME,'gtk-cursor-theme-name':NAME+'-Cursors'}))
    log=changes.state/'session.log'
    with log.open('a') as output:
        subprocess.Popen(['/usr/bin/python3',str(data/'runtime/session.py')],stdout=output,stderr=output,start_new_session=True)
        if shutil.which('conky'):subprocess.Popen(['conky','-c',str(config/'conky/Fire-Walk-With-Me.conf')],stdout=output,stderr=output,start_new_session=True)
    subprocess.run(['xfce4-panel','--restart'],check=True)

def install_system(changes, startup):
    share=Path('/usr/share');data=share/'fire-walk-with-me'
    for source in (ROOT/'.build/share').iterdir():
        if source.name in ['themes','icons']:
            for child in source.iterdir():changes.copy(child,share/source.name/child.name)
        else:changes.copy(source,share/source.name)
    channels=channel_defaults(data);channels['xfce4-panel']=panel_defaults(data)
    channels['xfce4-desktop']={'/backdrop/screen0/monitor0/workspace0/last-image':str(data/'wallpapers/red-room.png'),'/backdrop/screen0/monitor0/workspace0/image-style':5}
    for directory in [Path('/etc/xdg/xfce4'),Path('/etc/skel/.config/xfce4')]:
        for channel,values in channels.items():
            path=directory/'xfconf/xfce-perchannel-xml'/(channel+'.xml')
            if channel=='xfce4-panel':
                # A clean panel template excludes machine-specific tray history.
                content=xml_settings(Path('/nonexistent/fire-walk-with-me'),channel,values)
            else:content=xml_settings(path,channel,values)
            changes.text(path,content)
    setup_files(changes,Path('/etc/skel/.config'),data,startup)
    changes.text(Path('/etc/skel/.config/gtk-3.0/bookmarks'),'')
    changes.text(Path('/etc/skel/.config/xfce4/panel/docklike-2.rc'),
      '[user]\npinned=firefox;thunar;xfce4-terminal;\nindicatorStyle=2\nindicatorColor=rgb(165,197,139)\n')
    # Absolute skel Conky command must point to the shared template for future users.
    shared_conky=data/'conky.conf'
    changes.text(shared_conky,(ROOT/'profiles/conky.conf').read_text().replace('@DATA@',str(data)))
    for directory in [Path('/etc/xdg/autostart'),Path('/etc/skel/.config/autostart')]:
        changes.text(directory/'black-lodge-titles.desktop',desktop('Black Lodge Window Names',f'/usr/bin/python3 "{data}/runtime/session.py"'))
        if shutil.which('conky'):changes.text(directory/'conky.desktop',desktop('Firefox Walk With Me Clock',f'conky -c "{shared_conky}"'))
        if startup:changes.text(directory/'fire-walk-with-me-sound.desktop',desktop('Into the Lodge',f'paplay --volume=36000 "{data}/audio/into-the-lodge.wav"'))
    for version in ['gtk-3.0','gtk-4.0']:
        path=Path('/etc')/version/'settings.ini'
        changes.text(path,patch_ini(path,'Settings',{'gtk-theme-name':NAME,'gtk-icon-theme-name':NAME,'gtk-cursor-theme-name':NAME+'-Cursors'}))
    launchers(changes,Path('/usr/local/share/applications'))
    changes.text(Path('/usr/share/icons/default/index.theme'),'[Icon Theme]\nName=Default\nInherits='+NAME+'-Cursors\n')
    greeter=Path('/etc/lightdm/lightdm-gtk-greeter.conf')
    if greeter.exists():changes.text(greeter,patch_ini(greeter,'greeter',{
      'background':str(data/'wallpapers/red-room.png'),'user-background':'false',
      'theme-name':NAME,'icon-theme-name':NAME,'cursor-theme-name':NAME+'-Cursors',
      'font-name':'URW Gothic 11'}))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',action='store_true',help='Install system assets and defaults for new users; run with sudo.')
    parser.add_argument('--apply-only',action='store_true',help='Apply existing system assets to the current desktop.')
    parser.add_argument('--startup-sound',action='store_true',help='Enable the original desktop-login cue.')
    parser.add_argument('--fetch-chatgpt-logo',action='store_true',help='Fetch the pinned official mark for local composition.')
    parser.add_argument('--restore',action='store_true',help='Restore the saved files and touched desktop properties.')
    args=parser.parse_args()
    if args.system and os.geteuid()!=0:parser.error('--system requires sudo')
    if not args.system and os.geteuid()==0:parser.error('Run current-user installation without sudo.')
    if args.system and args.apply_only:parser.error('--system and --apply-only are mutually exclusive')
    state=Path('/var/lib/fire-walk-with-me') if args.system else Path.home()/'.local/state/fire-walk-with-me'
    changes=Changes(state)
    if args.restore:
        if not changes.journal.exists():raise SystemExit('No saved installation to restore.')
        if not args.system:
            stop_previous_helpers();service=xfconf()
            for channel,values in changes.records['xfconf'].items():
                for key,value in values.items():
                    if value is None:service.ResetProperty(channel,key,False)
                    else:service.SetProperty(channel,key,decode(value))
        changes.restore_files()
        changes.journal.rename(state/'restored.json')
        if not args.system:subprocess.run(['xfce4-panel','--restart'],check=True)
        print('Restored saved preferences and files. Log in again to reload previous autostart programs.');return
    if args.system:
        if not (ROOT/'.build/share/fire-walk-with-me/audio/into-the-lodge.wav').exists():
            parser.error('Build as your regular user first: python3 tools/build.py')
        if args.fetch_chatgpt_logo:parser.error('Fetch the optional logo during the regular-user build first.')
    elif not args.apply_only:
        from build import build
        build(args.fetch_chatgpt_logo)
    if args.system:install_system(changes,args.startup_sound)
    else:
        share=Path('/usr/share') if args.apply_only else Path.home()/'.local/share'
        if not args.apply_only:
            for source in (ROOT/'.build/share').iterdir():
                if source.name in ['themes','icons']:
                    for child in source.iterdir():changes.copy(child,share/source.name/child.name)
                else:changes.copy(source,share/source.name)
        apply_user(changes,share,args.startup_sound)
    print('Firefox Walk With Me installed. Private rollback:',changes.journal)

if __name__=='__main__':main()
