import hashlib
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from build_release import build
from novel import Book


class PackageTests(unittest.TestCase):
    def test_clean_repeatable_build_and_real_package_check(self):
        with tempfile.TemporaryDirectory(prefix='v61-build-test-') as tmp:
            out=Path(tmp)/'release'
            a=build(out)
            initial=(out/'初始化系统包.zip').read_bytes()
            complete=(out/'小说主V6_重建版.zip').read_bytes()
            (out/'web/obsolete.js').write_text('not part of this release')
            b=build(out)
            self.assertEqual(a['init_sha256'],b['init_sha256'])
            self.assertEqual(initial,(out/'初始化系统包.zip').read_bytes())
            self.assertEqual(complete,(out/'小说主V6_重建版.zip').read_bytes())
            self.assertFalse((out/'web/obsolete.js').exists())
            unpack=Path(tmp)/'unpack'
            with zipfile.ZipFile(out/'初始化系统包.zip') as z:z.extractall(unpack)
            self.assertEqual(Book(unpack).package_check()['status'],'package_ok')

    def test_source_and_unknown_web_directory_are_protected(self):
        with self.assertRaises(ValueError):
            build(ROOT)
        with tempfile.TemporaryDirectory(prefix='v61-build-protection-') as tmp:
            out=Path(tmp)/'release';(out/'web').mkdir(parents=True)
            keep=out/'web/user.txt';keep.write_text('keep')
            with self.assertRaises(ValueError):build(out)
            self.assertEqual(keep.read_text(),'keep')

    def test_changed_legacy_decoder_stops_release_instead_of_silently_skipping_fix(self):
        original=Path.read_text
        def changed(path,*args,**kwargs):
            value=original(path,*args,**kwargs)
            if path.name=='hub-core.mjs':
                value=value.replace("new TextDecoder('utf-8',{fatal:true})","new TextDecoder('utf-8')")
            return value
        with tempfile.TemporaryDirectory(prefix='v6-adapter-guard-') as tmp:
            with patch.object(Path,'read_text',changed):
                with self.assertRaisesRegex(ValueError,'兼容接口已变化'):
                    build(Path(tmp)/'release')


if __name__=='__main__':unittest.main()
