#!/usr/bin/python3
"""Give Thunar windows persistent display names, without changing the package."""
import sys

def display_title(name):
    if name.startswith('Black Lodge — '): return name
    return 'Black Lodge — ' + name.removesuffix(' - Thunar')

if sys.argv[1:] == ['--self-test']:
    assert display_title('Documents - Thunar') == 'Black Lodge — Documents'
    assert display_title('Black Lodge — Documents') == 'Black Lodge — Documents'
    assert display_title('Copying files') == 'Black Lodge — Copying files'
    print('Title formatting checks passed.')
    raise SystemExit

from pathlib import Path
import fcntl
import os
import signal
import gi
gi.require_version('Wnck', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkX11', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Wnck, Gdk, GdkX11, GLib, Gtk

lock_path = Path.home() / '.cache/black-lodge-titles.lock'
lock_path.parent.mkdir(parents=True, exist_ok=True)
lock = lock_path.open('a+')
try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError: raise SystemExit
lock.seek(0); lock.truncate(); lock.write(str(os.getpid())); lock.flush()
Gtk.init([])
display = Gdk.Display.get_default()
screen = Wnck.Screen.get_default()
original = {}

def rename(window):
    name = window.get_name()
    if not name or name.startswith('Black Lodge — '): return
    foreign = GdkX11.X11Window.foreign_new_for_display(display, window.get_xid())
    if foreign:
        original[window.get_xid()] = (foreign, name)
        foreign.set_title(display_title(name))
        display.flush()

def opened(_, window):
    if (window.get_class_group_name() or '').lower() != 'thunar': return
    window.connect('name-changed', rename)
    rename(window)

def stop():
    for foreign, name in original.values():
        if not foreign.is_destroyed(): foreign.set_title(name)
    display.flush()
    loop.quit()
    return GLib.SOURCE_REMOVE

screen.connect('window-opened', opened)
screen.connect('window-closed', lambda _, w: original.pop(w.get_xid(), None))
screen.force_update()
for window in screen.get_windows(): opened(screen, window)
loop = GLib.MainLoop()
GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, stop)
GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, stop)
loop.run()
