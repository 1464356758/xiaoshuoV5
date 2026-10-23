import copy, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns

class SeventhChapterRealReleaseTest(unittest.TestCase):
    def test_ch007_manuscript_evidence_and_state(self):
        root=ROOT/"book"
        state=ns.load_state(root)
        ns.verify_files(root,state)
        item=state["chapters"]["7"]
        body=(root/item["text_path"]).read_text(encoding="utf-8")
        record=ns.read_json(root/item["record_path"])
        gate=state["serialization"]["gates"]["7"]
        report=ns.read_json(root/gate["path"])
        self.assertEqual(ns.han_count(body),8605)
        self.assertEqual(ns.digest(body),item["text_sha256"])
        self.assertEqual(ns.digest(json.dumps(report,ensure_ascii=False,indent=2)+"\n"),gate["sha256"])
        self.assertEqual(len(report["checks"]),8)
        self.assertEqual([x["chapter"] for x in report["comparison"]],[4,5,6])
        self.assertEqual(report["read_coverage"],{k:state["chapters"][k]["text_sha256"] for k in ("4","5","6","7")})
        self.assertTrue(gate["used"])
        self.assertEqual(state["serialization"]["promises"]["P10"]["deadline_chapter"],8)
        self.assertEqual(state["serialization"]["promises"]["P02"]["deadline_chapter"],10)
        self.assertEqual(state["serialization"]["promises"]["P05"]["deadline_chapter"],50)
        self.assertFalse(state["serialization"]["published"])
        self.assertEqual(ns.review_status(state)["reviewed_until"],5)
        prior=copy.deepcopy(state)
        prior["chapters"]={k:v for k,v in prior["chapters"].items() if int(k)<=6}
        prior["tasks"]={k:v for k,v in prior["tasks"].items() if int(k)<=7}
        prior["revision"]=record["base_revision"]
        prior["tasks"]["7"]["phase"]="candidate"
        prior["serialization"]["frozen"].pop("7")
        prior["serialization"]["gates"]["7"]["used"]=False
        ns.serial_module().validate(root,prior,body,record,report,ns.serial_api())

if __name__=="__main__": unittest.main()
