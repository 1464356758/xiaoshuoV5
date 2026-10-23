import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns
class LiveCh014(unittest.TestCase):
 def test_frozen(self):
  root=ROOT/"book";s=ns.load_state(root);ns.verify_files(root,s)
  self.assertGreaterEqual(len(s["chapters"]),14)
  item=s["chapters"]["14"];body=(root/item["text_path"]).read_text(encoding="utf-8")
  r=ns.read_json(root/s["serialization"]["gates"]["14"]["path"])
  self.assertEqual(ns.han_count(body),8811)
  self.assertEqual(ns.digest(body),item["text_sha256"])
  self.assertTrue(s["serialization"]["gates"]["14"]["used"])
  self.assertEqual(set(r["checks"]),{"timeline","knowledge","props_resources","causality","power_rules","promises","anti_repeat","character_agency"})
  self.assertEqual([x["chapter"] for x in r["comparison"]],[11,12,13])
  self.assertEqual(r["read_coverage"],{str(n):s["chapters"][str(n)]["text_sha256"] for n in range(11,15)})
  self.assertEqual(s["serialization"]["promises"]["P11"]["deadline_chapter"],15)
  self.assertIn("银行返回这笔十月旧指令的明确拒绝处理回执",body)
  self.assertFalse(s["serialization"]["published"])
