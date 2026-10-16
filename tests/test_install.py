"""Exercise rollback with existing, missing, and symlinked assets; preserve unrelated XML."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

spec=importlib.util.spec_from_file_location('installer',Path(__file__).resolve().parents[1]/'tools/install.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class InstallerTests(unittest.TestCase):
    def test_rollback_and_repeat_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);changes=m.Changes(root/'state')
            original=root/'original';original.write_text('retain')
            link=root/'link';link.symlink_to(original)
            folder=root/'theme';folder.mkdir();(folder/'old').write_text('old')
            source=root/'source';source.mkdir();(source/'new').write_text('new')
            created=root/'created'
            changes.text(link,'replacement');changes.text(created,'new');changes.copy(source,folder)
            self.assertEqual(original.read_text(),'retain')
            m.Changes(root/'state').text(link,'second install')
            restored=m.Changes(root/'state');restored.restore_files()
            self.assertTrue(link.is_symlink());self.assertEqual(link.resolve(),original)
            self.assertFalse(created.exists());self.assertEqual((folder/'old').read_text(),'old')
            self.assertFalse((folder/'new').exists())
            restored.journal.rename(root/'state/restored.json')
            fresh=m.Changes(root/'state');fresh.text(link,'new cycle');fresh.restore_files()
            self.assertTrue(link.is_symlink());self.assertEqual(original.read_text(),'retain')

    def test_xml_retains_scaling_and_power(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'settings.xml'
            path.write_text('<channel name="test"><property name="Gdk" type="empty"><property name="WindowScalingFactor" type="int" value="2"/></property><property name="idle-on-ac" type="int" value="0"/></channel>')
            result=ET.fromstring(m.xml_settings(path,'test',{'/Net/ThemeName':m.NAME,'/panels':[1],'/enabled':True}))
            self.assertEqual(result.find("./property[@name='Gdk']/property").get('value'),'2')
            self.assertEqual(result.find("./property[@name='idle-on-ac']").get('value'),'0')
            self.assertEqual(result.find("./property[@name='panels']/value").get('value'),'1')
            self.assertEqual(result.find("./property[@name='enabled']").get('type'),'bool')

    def test_typed_xfconf_roundtrip(self):
        import dbus
        for value in [dbus.UInt32(44),dbus.Boolean(True),dbus.Double(.5),dbus.String('Lodge'),dbus.Array([dbus.Int32(1),dbus.Int32(20)],signature='v')]:
            restored=m.decode(m.encode(value))
            self.assertEqual(type(restored),type(value));self.assertEqual(restored,value)

if __name__=='__main__':unittest.main()
