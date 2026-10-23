import copy, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns

class NinthChapterRefundEvidenceTest(unittest.TestCase):
    def test_ch009_legal_double_source_pending_bank_execution(self):
        book=ROOT/"book"
        state=ns.load_state(book)
        ns.verify_files(book,state)
        item=state["chapters"]["9"]
        body=(book/item["text_path"]).read_text(encoding="utf-8")
        record=ns.read_json(book/item["record_path"])
        gate=state["serialization"]["gates"]["9"]
        report=ns.read_json(book/gate["path"])
        self.assertEqual(ns.han_count(body),8876)
        self.assertEqual(ns.digest(body),item["text_sha256"])
        self.assertEqual(ns.digest(json.dumps(report,ensure_ascii=False,indent=2)+"\n"),gate["sha256"])
        self.assertTrue(gate["used"])
        self.assertEqual(report["decision"],"release")
        self.assertEqual(len(report["checks"]),8)
        self.assertEqual([x["chapter"] for x in report["comparison"]],[6,7,8])
        self.assertEqual(report["read_coverage"],{k:state["chapters"][k]["text_sha256"] for k in ("6","7","8","9")})
        self.assertEqual(state["serialization"]["promises"]["P02"]["status"],"open")
        self.assertEqual(state["serialization"]["promises"]["P02"]["deadline_chapter"],10)
        self.assertEqual(state["serialization"]["promises"]["P10"]["status"],"closed")
        self.assertFalse(state["serialization"]["published"])
        self.assertEqual(ns.review_status(state)["reviewed_until"],5)
        self.assertIn("支付准备区",body)
        self.assertIn("原指令到底有没有被银行接纳",body)
        old=copy.deepcopy(state)
        old["chapters"]={k:v for k,v in old["chapters"].items() if int(k)<=8}
        old["tasks"]={k:v for k,v in old["tasks"].items() if int(k)<=9}
        old["revision"]=record["base_revision"]
        old["tasks"]["9"]["phase"]="candidate"
        old["serialization"]["frozen"].pop("9")
        old["serialization"]["gates"]["9"]["used"]=False
        for p in old["serialization"]["promises"].values():
            if p.get("last_reviewed_chapter")==9: p["last_reviewed_chapter"]=8
        ns.serial_module().validate(book,old,body,record,report,ns.serial_api())

if __name__=="__main__":
    unittest.main()
