#!/usr/bin/env python3
"""Focused checks of built native assets, independent of desktop preferences."""
from array import array
import ctypes
import json
import os
from pathlib import Path
import subprocess
import wave
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SHARE=ROOT/'.build/share'

def main():
    for path in SHARE.rglob('*.svg'):ET.parse(path)
    links=[p for p in SHARE.rglob('*') if p.is_symlink()]
    assert links and all(path.exists() for path in links),'Broken aliases'
    for version in ['3.0','4.0']:
        code=f'''import gi
gi.require_version('Gtk','{version}');from gi.repository import Gtk
p=Gtk.CssProvider();errors=[]
p.connect('parsing-error',lambda p,s,e:errors.append(str(e)))
p.load_from_path({str(SHARE/'themes/Fire-Walk-With-Me'/('gtk-'+version)/'gtk.css')!r})
assert not errors,errors
'''
        subprocess.run(['python3','-c',code],check=True)
    import gi
    gi.require_version('Gtk','3.0')
    from gi.repository import Gtk
    theme=Gtk.IconTheme.new();theme.prepend_search_path(str(SHARE/'icons'));theme.set_custom_theme('Fire-Walk-With-Me')
    aliases=['fire-walk-with-me','start-here','avatar-default','folder','folder-documents','folder-pictures','folder-downloads','folder-music','folder-videos','text-plain','utilities-terminal','firefox','google-chrome']
    if (SHARE/'icons/Fire-Walk-With-Me/scalable/apps/codex-desktop.svg').exists():aliases.append('codex-desktop')
    # Test available composites; a build without the optional official mark inherits it.
    for name in aliases:
        for size in [16,24,48,96]:
            info=theme.lookup_icon(name,size,Gtk.IconLookupFlags.FORCE_SIZE)
            assert info is not None,(name,size)
            pixbuf=info.load_icon();assert pixbuf.get_width()>0,(name,size)
    filenames=[theme.lookup_icon(name,48,0).get_filename() for name in ['folder-documents','folder-pictures','folder-downloads','folder-music','folder-videos']]
    assert len({str(Path(p).resolve()) for p in filenames})==5
    class Cursor(ctypes.Structure):
        _fields_=[('version',ctypes.c_uint),('size',ctypes.c_uint),('width',ctypes.c_uint),('height',ctypes.c_uint),('xhot',ctypes.c_uint),('yhot',ctypes.c_uint),('delay',ctypes.c_uint),('pixels',ctypes.POINTER(ctypes.c_uint))]
    lib=ctypes.CDLL('libXcursor.so.1')
    lib.XcursorFilenameLoadImage.argtypes=[ctypes.c_char_p,ctypes.c_int];lib.XcursorFilenameLoadImage.restype=ctypes.POINTER(Cursor)
    lib.XcursorImageDestroy.argtypes=[ctypes.POINTER(Cursor)]
    for path in (SHARE/'icons/Fire-Walk-With-Me-Cursors/cursors').iterdir():
        for size in [24,32,48,64]:
            cursor=lib.XcursorFilenameLoadImage(os.fsencode(path),size);assert cursor,path
            value=cursor.contents
            assert value.width==value.height==size,(path,size)
            assert value.xhot<size and value.yhot<size,(path,size)
            lib.XcursorImageDestroy(cursor)
    with wave.open(str(SHARE/'fire-walk-with-me/audio/into-the-lodge.wav'),'rb') as source:
        assert source.getnchannels()==2 and source.getframerate()==48000 and source.getsampwidth()==2
        assert abs(source.getnframes()/48000-6.4)<.001
        pcm=array('h',source.readframes(source.getnframes()))
        assert max(abs(x) for x in pcm)<=16384
        assert pcm[0]==pcm[1]==pcm[-1]==pcm[-2]==0
    subprocess.run(['python3',str(ROOT/'runtime/window-names.py'),'--self-test'],check=True)
    subprocess.run(['python3','-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],check=True)
    print(json.dumps({'result':'VERIFIED','css':['GTK3','GTK4'],'icon_sizes':[16,24,48,96],
      'distinct_special_folders':5,'cursor_sizes':[24,32,48,64],
      'audio':'6.4s stereo 48kHz; peak ≤ -6dBFS; silent endpoints',
      'rollback':'files, symlinks, repeated install, typed desktop properties'},indent=2))

if __name__=='__main__':main()
