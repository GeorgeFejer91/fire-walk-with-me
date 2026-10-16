#!/usr/bin/python3
"""Select matching native window decorations and name Thunar windows at login."""
from pathlib import Path
import subprocess
import sys
import gi
gi.require_version('Gdk','3.0')
from gi.repository import Gdk

theme=subprocess.run(['xfconf-query','-c','xfwm4','-p','/general/theme'],capture_output=True,text=True).stdout.strip()
if theme in ['Fire-Walk-With-Me','Fire-Walk-With-Me-HiDPI']:
    display=Gdk.Display.get_default()
    scale=display.get_monitor(0).get_scale_factor() if display else 1
    subprocess.run(['xfconf-query','-c','xfwm4','-p','/general/theme','-s','Fire-Walk-With-Me'+('-HiDPI' if scale>=2 else '')],check=True)
    # XFCE aligns this shared image across external plugin windows.
    import dbus
    service=dbus.Interface(dbus.SessionBus().get_object('org.xfce.Xfconf','/org/xfce/Xfconf'),'org.xfce.Xfconf')
    marker=Path.home()/'.local/state/fire-walk-with-me/wallpaper-initialized'
    if not marker.exists():
        screen=Gdk.Screen.get_default()
        image=Path(__file__).resolve().parents[1]/'wallpapers/red-room.png'
        for index in range(display.get_n_monitors()):
            monitor=screen.get_monitor_plug_name(index) or str(index)
            prefix=f'/backdrop/screen0/monitor{monitor}/workspace0/'
            service.SetProperty('xfce4-desktop',prefix+'last-image',dbus.String(str(image)))
            service.SetProperty('xfce4-desktop',prefix+'image-style',dbus.Int32(5))
        service.SetProperty('xfce4-desktop','/backdrop/single-workspace-mode',dbus.Boolean(True))
        service.SetProperty('xfce4-desktop','/backdrop/single-workspace-number',dbus.Int32(0))
        marker.parent.mkdir(parents=True,exist_ok=True);marker.write_text('Initialized first-login wallpaper.\n')
        from gi.repository import GLib
        bookmarks=Path.home()/'.config/gtk-3.0/bookmarks'
        if not bookmarks.exists() or not bookmarks.read_text().strip():
            rows=[]
            for kind in [GLib.UserDirectory.DIRECTORY_DOCUMENTS,GLib.UserDirectory.DIRECTORY_PICTURES,GLib.UserDirectory.DIRECTORY_MUSIC,GLib.UserDirectory.DIRECTORY_VIDEOS,GLib.UserDirectory.DIRECTORY_DOWNLOAD]:
                directory=GLib.get_user_special_dir(kind)
                if directory and Path(directory)!=Path.home():rows.append(Path(directory).as_uri())
            bookmarks.parent.mkdir(parents=True,exist_ok=True);bookmarks.write_text('\n'.join(rows)+'\n')
    for key,value in service.GetAllProperties('xfce4-panel','/').items():
        if key.endswith('/background-image') and 'fire-walk-with-me/identity/panel-surface' in str(value):
            image=Path(__file__).resolve().parents[1]/'identity'/('panel-surface'+('-2x' if scale>=2 else '')+'.png')
            service.SetProperty('xfce4-panel',key,dbus.String(str(image)))
import os
os.execv(sys.executable,[sys.executable,str(Path(__file__).with_name('window-names.py'))])
