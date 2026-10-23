import copy, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns

class EighthChapterP10ReleaseTest(unittest.TestCase):
    def test_ch008_actual_payments_and_deadline(self):
        root=ROOT/"book"
        state=ns.load_state(root)
        ns.verify_files(root,state)
        item=state["chapters"]["8"]
        text=(root/item["text_path"]).read_text(encoding="utf-8")
        record=ns.read_json(root/item["record_path"])
        gate=state["serialization"]["gates"]["8"]
        report=ns.read_json(root/gate["path"])
        self.assertEqual(ns.han_count(text),8546)
        self.assertEqual(ns.digest(text),item["text_sha256"])
        self.assertEqual(ns.digest(json.dumps(report,ensure_ascii=False,indent=2)+"\n"),gate["sha256"])
        self.assertEqual(report["decision"],"release")
        self.assertEqual(len(report["checks"]),8)
        self.assertEqual([x["chapter"] for x in report["comparison"]],[5,6,7])
        self.assertEqual(report["read_coverage"],{k:state["chapters"][k]["text_sha256"] for k in ("5","6","7","8")})
        self.assertTrue(gate["used"])
        self.assertEqual(state["serialization"]["promises"]["P10"]["deadline_chapter"],8)
        self.assertEqual(state["serialization"]["promises"]["P10"]["status"],"closed")
        self.assertEqual(state["serialization"]["promises"]["P02"]["deadline_chapter"],10)
        self.assertEqual(state["serialization"]["promises"]["P02"]["status"],"open")
        self.assertFalse(state["serialization"]["published"])
        self.assertEqual(ns.review_status(state)["reviewed_until"],5)
        self.assertIn("三百元",text)
        self.assertIn("二千八百七十元",text)
        before=copy.deepcopy(state)
        before["chapters"]={k:v for k,v in before["chapters"].items() if int(k)<=7}
        before["tasks"]={k:v for k,v in before["tasks"].items() if int(k)<=8}
        before["revision"]=record["base_revision"]
        before["tasks"]["8"]["phase"]="candidate"
        before["serialization"]["frozen"].pop("8")
        before["serialization"]["gates"]["8"]["used"]=False
        for promise in before["serialization"]["promises"].values():
            if promise.get("last_reviewed_chapter")==8:
                promise["last_reviewed_chapter"]=7
            promise["history"]=[e for e in promise.get("history",[]) if e.get("chapter",0)<8]
        before["serialization"]["promises"]["P10"]["status"]="open"
        ns.serial_module().validate(root,before,text,record,report,ns.serial_api())

if __name__=="__main__": unittest.main()
