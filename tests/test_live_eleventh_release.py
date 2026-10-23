import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns
class ElevenChapterFrozenTest(unittest.TestCase):
 def test_live_ch011_evidence_and_release(self):
  root=ROOT/"book"
  state=ns.load_state(root)
  ns.verify_files(root,state)
  item=state["chapters"]["11"]
  body=(root/item["text_path"]).read_text(encoding="utf-8")
  record=ns.read_json(root/item["record_path"])
  report=ns.read_json(root/state["serialization"]["gates"]["11"]["path"])
  self.assertEqual(ns.han_count(body),8803)
  self.assertEqual(ns.digest(body),item["text_sha256"])
  self.assertEqual(record["stage"],"S02")
  self.assertEqual([v["chapter"] for v in report["comparison"]],[8,9,10])
  self.assertEqual(report["read_coverage"],{str(n):state["chapters"][str(n)]["text_sha256"] for n in range(8,12)})
  self.assertEqual(set(report["checks"]),{"timeline","knowledge","props_resources","causality","power_rules","promises","anti_repeat","character_agency"})
  self.assertEqual(next(x for x in report["promise_reviews"] if x["id"]=="P04")["action"],"keep")
  self.assertEqual(next(x for x in report["promise_reviews"] if x["id"]=="P11")["deadline_chapter"],15)
  self.assertTrue(state["serialization"]["gates"]["11"]["used"])
  self.assertGreaterEqual(ns.review_status(state)["reviewed_until"],10)
  self.assertIn("监督议题申请已被登记受理",body)
  self.assertIn("负责人按正式结算渠道确认到账",body)
