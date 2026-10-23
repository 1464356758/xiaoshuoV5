import copy, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns

class RealSixthReleaseTest(unittest.TestCase):
    def test_ch006_release_and_continuity(self):
        book=ROOT/"book"
        state=ns.load_state(book)
        ns.verify_files(book,state)
        self.assertGreaterEqual(len(state["chapters"]),6)
        item=state["chapters"]["6"]
        body=(book/item["text_path"]).read_text(encoding="utf-8")
        rec=ns.read_json(book/item["record_path"])
        gate=state["serialization"]["gates"]["6"]
        report=ns.read_json(book/gate["path"])
        self.assertEqual(ns.han_count(body),8929)
        self.assertEqual(ns.digest(body),item["text_sha256"])
        self.assertEqual(ns.digest(json.dumps(report,ensure_ascii=False,indent=2)+"\n"),gate["sha256"])
        self.assertTrue(gate["used"])
        self.assertEqual(report["read_coverage"],{k:state["chapters"][k]["text_sha256"] for k in ("3","4","5","6")})
        self.assertEqual(len(report["checks"]),8)
        self.assertEqual([x["chapter"] for x in report["comparison"]],[3,4,5])
        self.assertEqual(state["serialization"]["promises"]["P10"]["deadline_chapter"],8)
        self.assertEqual(state["serialization"]["promises"]["P02"]["deadline_chapter"],10)
        self.assertEqual(state["serialization"]["promises"]["P03"]["status"],"closed")
        self.assertEqual(state["serialization"]["promises"]["P08"]["status"],"open")
        self.assertEqual(len(state["serialization"]["published"]),0)
        self.assertGreaterEqual(ns.review_status(state)["reviewed_until"],5)
        before=copy.deepcopy(state)
        before["chapters"]={k:v for k,v in before["chapters"].items() if int(k)<=5}
        before["tasks"]={k:v for k,v in before["tasks"].items() if int(k)<=6}
        before["revision"]=rec["base_revision"]
        before["tasks"]["6"]["phase"]="candidate"
        before["serialization"]["frozen"].pop("6")
        before["serialization"]["gates"]["6"]["used"]=False
        before["serialization"]["promises"].pop("P10")
        ns.serial_module().validate(book,before,body,rec,report,ns.serial_api())

if __name__=="__main__": unittest.main()
