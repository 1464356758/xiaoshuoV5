import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns

class FifteenthWindowRelease(unittest.TestCase):
    def test_frozen_and_five_chapter_review(self):
        book=ROOT/"book"
        state=ns.load_state(book)
        ns.verify_files(book,state)
        self.assertGreaterEqual(len(state["chapters"]),15)
        item=state["chapters"]["15"]
        body=(book/item["text_path"]).read_text(encoding="utf-8")
        record=ns.read_json(book/item["record_path"])
        gate=state["serialization"]["gates"]["15"]
        report=ns.read_json(book/gate["path"])
        self.assertEqual(ns.han_count(body),9031)
        self.assertEqual(ns.digest(body),item["text_sha256"])
        self.assertEqual(ns.digest((book/item["record_path"]).read_text(encoding="utf-8")),item["record_sha256"])
        self.assertTrue(gate["used"])
        self.assertEqual(set(report["checks"]),{"timeline","knowledge","props_resources","causality","power_rules","promises","anti_repeat","character_agency"})
        self.assertEqual([c["chapter"] for c in report["comparison"]],[12,13,14])
        self.assertEqual(report["read_coverage"],{str(n):state["chapters"][str(n)]["text_sha256"] for n in range(12,16)})
        cp=report["checkpoint"]
        self.assertEqual((cp["kind"],cp["from"],cp["to"]),("window",11,15))
        self.assertEqual(cp["read_mode"],"full_text_batches")
        self.assertEqual(cp["coverage"],{str(n):state["chapters"][str(n)]["text_sha256"] for n in range(11,16)})
        self.assertEqual(cp["record_coverage"],{str(n):state["chapters"][str(n)]["record_sha256"] for n in range(11,16)})
        self.assertTrue(any(c.get("from")==11 and c.get("to")==15 for c in state["checkpoints"]))
        self.assertEqual(state["serialization"]["promises"]["P11"]["status"],"closed")
        self.assertEqual(state["serialization"]["promises"]["P13"]["deadline_chapter"],19)
        self.assertEqual(state["serialization"]["promises"]["P13"]["status"],"open")
        self.assertIn("银行返回了有确定交易标识的执行成功回执",body)
        self.assertIn("季秀兰自己读过金额与来源，点头确认",body)
        self.assertFalse(state["serialization"]["published"])
