import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns

class FirstFiveChapterCheckpointTest(unittest.TestCase):
    def test_live_fifth_release_and_five_chapter_review(self):
        book=ROOT/"book"
        state=ns.load_state(book)
        ns.verify_files(book,state)
        self.assertGreaterEqual(len(state["chapters"]),5)
        item=state["chapters"]["5"]
        body=(book/item["text_path"]).read_text(encoding="utf-8")
        record=ns.read_json(book/item["record_path"])
        gate=state["serialization"]["gates"]["5"]
        report=ns.read_json(book/gate["path"])
        self.assertEqual(ns.han_count(body),9039)
        self.assertEqual(ns.digest(body),item["text_sha256"])
        self.assertEqual(ns.digest(json.dumps(report,ensure_ascii=False,indent=2)+"\n"),gate["sha256"])
        self.assertTrue(gate["used"])
        self.assertEqual(report["read_coverage"]["5"],item["text_sha256"])
        self.assertEqual(len(report["checks"]),8)
        self.assertEqual(len(report["comparison"]),3)
        cp=report["checkpoint"]
        self.assertEqual((cp["kind"],cp["from"],cp["to"]),("window",1,5))
        self.assertEqual(cp["decision"],"continue")
        self.assertEqual(cp["read_mode"],"full_text_batches")
        self.assertEqual(cp["coverage"],{k:v["text_sha256"] for k,v in state["chapters"].items() if int(k)<=5})
        self.assertEqual(cp["record_coverage"],{k:v["record_sha256"] for k,v in state["chapters"].items() if int(k)<=5})
        self.assertTrue(any(x==cp for x in state["checkpoints"]))
        self.assertGreaterEqual(ns.review_status(state)["reviewed_until"],5)
        self.assertEqual(state["serialization"]["promises"]["P03"]["status"],"closed")
        self.assertEqual(state["serialization"]["promises"]["P09"]["deadline_chapter"],95)
        self.assertEqual(state["serialization"]["promises"]["P08"]["status"],"open")
        self.assertFalse(state["serialization"]["published"])
        old=copy.deepcopy(state)
        old["chapters"]={k:v for k,v in old["chapters"].items() if int(k)<=4}
        old["tasks"]={k:v for k,v in old["tasks"].items() if int(k)<=5}
        old["revision"]=record["base_revision"]
        old["checkpoints"]=[]
        old["tasks"]["5"]["phase"]="candidate"
        old["serialization"]["frozen"].pop("5")
        old["serialization"]["gates"]["5"]["used"]=False
        old["serialization"]["promises"].pop("P09")
        old["serialization"]["promises"]["P03"]["status"]="open"
        old["serialization"]["promises"]["P03"]["last_reviewed_chapter"]=4
        ns.serial_module().validate(book,old,body,record,report,ns.serial_api())

if __name__=="__main__":
    unittest.main()
