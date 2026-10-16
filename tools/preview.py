#!/usr/bin/env python3
"""Capture real XFCE screens in a disposable, private-data-free X11 session."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]

def run(*args, **kwargs):return subprocess.run(args,check=True,**kwargs)

def capture(scale, output):
    from install import xml_settings,panel_defaults,channel_defaults
    home=Path.home();config=home/'.config';data=Path('/usr/share/fire-walk-with-me')
    channels=channel_defaults(data)
    channels['xsettings']['/Gdk/WindowScalingFactor']=scale
    channels['xsettings']['/Gtk/FontName']='Noto Sans 10'
    channels['xfwm4']['/general/theme']='Fire-Walk-With-Me'+('-HiDPI' if scale==2 else '')
    channels['xfce4-panel']=panel_defaults(data)
    channels['xfce4-panel']['/panels/panel-1/background-image']=str(data/'identity'/('panel-surface'+('-2x' if scale==2 else '')+'.png'))
    channels['xfce4-panel']['/plugins/plugin-20/profile-shape']=2
    channels['xfce4-desktop']={'/desktop-icons/file-icons/show-home':True,'/desktop-icons/file-icons/show-trash':True,'/desktop-icons/icon-size':40}
    channels['xfce4-desktop']['/desktop-icons/file-icons/show-removable']=False
    for channel,values in channels.items():
        path=config/'xfce4/xfconf/xfce-perchannel-xml'/(channel+'.xml');path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(xml_settings(Path('/nonexistent/fire-walk-with-me'),channel,values))
    directories=['Desktop','Documents','Downloads','Music','Pictures','Public','Templates','Videos']
    for name in directories:(home/name).mkdir()
    keys={'Downloads':'DOWNLOAD','Public':'PUBLICSHARE'}
    (config/'user-dirs.dirs').write_text(''.join(f'XDG_{keys.get(name,name.upper())}_DIR="$HOME/{name}"\n' for name in directories))
    (home/'Documents/Field Notes.txt').write_text('FIRE WALK WITH ME\n\nNative XFCE desktop skin.\nVelvet, chevrons, and green opening-title lettering.\n')
    shutil.copy2(ROOT/'assets/identity/owl-cave.svg',home/'Pictures/Owl Cave.svg')
    path=config/'xfce4/panel/docklike-2.rc';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('[user]\npinned=firefox;thunar;xfce4-terminal;\nindicatorStyle=2\nindicatorColor=rgb(165,197,139)\n')
    from install import terminal
    path=config/'xfce4/terminal/terminalrc';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(terminal(path))
    output.mkdir(parents=True,exist_ok=True)
    processes=[]
    log=(output/'preview.log').open('w')
    try:
        for command in [['xfsettingsd','--no-daemon'],['xfwm4','--compositor=on'],['xfdesktop','--disable-wm-check'],['xfce4-panel','--disable-wm-check']]:
            processes.append(subprocess.Popen(command,stdout=log,stderr=log));time.sleep(.5)
        import dbus
        service=dbus.Interface(dbus.SessionBus().get_object('org.xfce.Xfconf','/org/xfce/Xfconf'),'org.xfce.Xfconf')
        for key in service.GetAllProperties('xfce4-desktop','/'):
            if key.endswith('/last-image'):service.SetProperty('xfce4-desktop',key,dbus.String(str(data/'wallpapers/red-room.png')))
            if key.endswith('/image-style'):service.SetProperty('xfce4-desktop',key,dbus.Int32(5))
        run('xfdesktop','--reload',stdout=log,stderr=log);time.sleep(.8)
        processes.append(subprocess.Popen(['python3',str(data/'runtime/session.py')],stdout=log,stderr=log))
        processes.append(subprocess.Popen(['conky','-c',str(data/'conky.conf')],stdout=log,stderr=log))
        time.sleep(1)
        def shot(name):
            run('xdotool','mousemove','5','5');time.sleep(.3)
            run('scrot','-o','-q','90',str(output/(name+'.jpg')));print('Captured',name,flush=True)
        shot('desktop')
        run('xfce4-popup-whiskermenu');time.sleep(.5);shot('start-menu');run('xdotool','key','Escape')
        processes.append(subprocess.Popen(['thunar','-w',str(home)],stdout=log,stderr=log));time.sleep(1)
        lines=subprocess.check_output(['wmctrl','-lx'],text=True).splitlines()
        wid=next(line.split()[0] for line in lines if 'thunar.thunar' in line.lower())
        width,height=(1920,1200) if scale==1 else (2560,1600)
        run('wmctrl','-ir',wid,'-b','remove,maximized_vert,maximized_horz')
        run('wmctrl','-ir',wid,'-e',f'0,{80*scale},{65*scale},{min(1000*scale,width-180)},{min(650*scale,height-250)}')
        time.sleep(.5);shot('files')
        run('xdotool','windowactivate','--sync',wid);run('xdotool','key','ctrl+l')
        run('xdotool','type','--clearmodifiers',str(home/'Documents'));run('xdotool','key','Return');time.sleep(.4)
        shot('documents')
        run('xdotool','key','ctrl+a');time.sleep(.2);shot('file-selected')
        run('xdotool','key','ctrl+shift+n');time.sleep(.4);shot('dialog');run('xdotool','key','Escape')
        run('wmctrl','-ic',wid)
        demo=home/'terminal-demo.py'
        demo.write_text("import time\nprint('FIRE WALK WITH ME\\n')\nprint('SYSTEM ONLINE   /   THE LODGE IS OPEN\\n')\nprint('Native windows. Familiar controls. Something in the woods.\\n')\nprint('  [OK] velvet / chevron panel')\nprint('  [OK] Owl Cave start mark')\nprint('  [OK] original synth login cue')\nprint('\\nReady.\\n')\ntime.sleep(120)\n")
        processes.append(subprocess.Popen(['xfce4-terminal','--disable-server','--title=Red Room Terminal','--geometry=90x24','--command=python3 '+str(demo)],stdout=log,stderr=log));time.sleep(.8);shot('terminal')
        print('Native screenshots complete.',flush=True)
    finally:
        for process in reversed(processes):
            if process.poll() is None:process.terminate()
        log.close()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--scale',type=int,choices=[1,2],default=2)
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/preview-2x');parser.add_argument('--inside',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.output.resolve()
    if args.inside:capture(args.scale,output);return
    (ROOT/'.build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='Lodge-') as temporary:
        home=Path(temporary)/'Lodge';home.mkdir()
        env=os.environ.copy();env['HOME']=str(home)
        for variable,suffix in [('XDG_CONFIG_HOME','.config'),('XDG_CACHE_HOME','.cache'),('XDG_DATA_HOME','.local/share'),('XDG_RUNTIME_DIR','run')]:
            path=(Path(temporary) if variable=='XDG_RUNTIME_DIR' else home)/suffix
            path.mkdir(parents=True,exist_ok=True,mode=0o700);env[variable]=str(path)
        for variable in ['DBUS_SESSION_BUS_ADDRESS','SESSION_MANAGER','GDK_SCALE','GDK_DPI_SCALE','GTK_THEME']:env.pop(variable,None)
        env['GIO_USE_VFS']='local';env['GVFS_DISABLE_FUSE']='1'
        size='1920x1200x24' if args.scale==1 else '2560x1600x24'
        try:
            run('xvfb-run','-a','-s','-screen 0 '+size,'dbus-run-session','--','python3',str(Path(__file__).resolve()),'--inside','--scale',str(args.scale),'--output',str(output),env=env)
        finally:
            for mount in [Path(temporary)/'run/doc',Path(temporary)/'run/gvfs']:
                if mount.is_mount():subprocess.run(['fusermount3','-u',str(mount)],capture_output=True)
            time.sleep(1)

if __name__=='__main__':main()
