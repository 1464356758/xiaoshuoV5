import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns
class ChapterTwelveFrozenTest(unittest.TestCase):
 def test_ch012_version_integrity(self):
  book=ROOT/"book";st=ns.load_state(book);ns.verify_files(book,st)
  self.assertGreaterEqual(len(st["chapters"]),12)
  c=st["chapters"]["12"];body=(book/c["text_path"]).read_text(encoding="utf-8")
  report=ns.read_json(book/st["serialization"]["gates"]["12"]["path"])
  self.assertEqual(ns.han_count(body),8561)
  self.assertEqual(ns.digest(body),c["text_sha256"])
  self.assertEqual(c["stage"],"S02")
  self.assertTrue(st["serialization"]["gates"]["12"]["used"])
  self.assertEqual(set(report["checks"]),{"timeline","knowledge","props_resources","causality","power_rules","promises","anti_repeat","character_agency"})
  self.assertEqual([x["chapter"] for x in report["comparison"]],[9,10,11])
  self.assertEqual(report["read_coverage"],{str(i):st["chapters"][str(i)]["text_sha256"] for i in (9,10,11,12)})
  self.assertEqual(st["serialization"]["promises"]["P04"]["deadline_chapter"],20)
  self.assertEqual(st["serialization"]["promises"]["P11"]["deadline_chapter"],15)
  self.assertIn("由接件系统形成新的收到回执",body)
  self.assertIn("董事实际阅看范围仍不完整",body)
  self.assertFalse(st["serialization"]["published"])
