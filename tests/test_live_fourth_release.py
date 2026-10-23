import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns

class RealFourthReleaseTest(unittest.TestCase):
    def test_ch004_release_and_evidence(self):
        book=ROOT/"book"
        state=ns.load_state(book)
        ns.verify_files(book,state)
        self.assertGreaterEqual(len(state["chapters"]),4)
        item=state["chapters"]["4"]
        body=(book/item["text_path"]).read_text(encoding="utf-8")
        record=ns.read_json(book/item["record_path"])
        gate=state["serialization"]["gates"]["4"]
        report=ns.read_json(book/gate["path"])
        self.assertEqual(ns.han_count(body),9143)
        self.assertEqual(ns.digest(body),item["text_sha256"])
        self.assertEqual(ns.digest(json.dumps(report,ensure_ascii=False,indent=2)+"\n"),gate["sha256"])
        self.assertTrue(gate["used"])
        self.assertEqual(len(report["comparison"]),3)
        self.assertEqual(state["serialization"]["promises"]["P03"]["deadline_chapter"],5)
        self.assertEqual(state["serialization"]["promises"]["P01A"]["status"],"closed")
        self.assertEqual(len(state["serialization"]["published"]),0)
        prior=copy.deepcopy(state)
        prior["chapters"]={k:v for k,v in prior["chapters"].items() if int(k)<=3}
        prior["tasks"]={k:v for k,v in prior["tasks"].items() if int(k)<=4}
        prior["revision"]=record["base_revision"]
        prior["tasks"]["4"]["phase"]="candidate"
        prior["serialization"]["frozen"]={k:v for k,v in prior["serialization"]["frozen"].items() if int(k)<=3}
        prior["serialization"]["gates"]={k:v for k,v in prior["serialization"]["gates"].items() if int(k)<=4}
        prior["serialization"]["gates"]["4"]["used"]=False
        ns.serial_module().validate(book,prior,body,record,report,ns.serial_api())

if __name__=="__main__":
    unittest.main()
