import copy, unittest, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns

class ChapterThirteenRelease(unittest.TestCase):
    def test_live_ch013(self):
        root=ROOT/"book";state=ns.load_state(root);ns.verify_files(root,state)
        self.assertGreaterEqual(len(state["chapters"]),13)
        item=state["chapters"]["13"]
        body=(root/item["text_path"]).read_text(encoding="utf-8")
        rec=ns.read_json(root/item["record_path"])
        gate=state["serialization"]["gates"]["13"]
        report=ns.read_json(root/gate["path"])
        self.assertEqual(ns.han_count(body),9121)
        self.assertEqual(ns.digest(body),item["text_sha256"])
        self.assertEqual(rec["text_sha256"],item["text_sha256"])
        self.assertEqual(rec["stage"],"S02")
        self.assertTrue(gate["used"])
        self.assertEqual(set(report["checks"]),{"timeline","knowledge","props_resources","causality","power_rules","promises","anti_repeat","character_agency"})
        self.assertEqual([x["chapter"] for x in report["comparison"]],[10,11,12])
        self.assertEqual(report["read_coverage"],{str(n):state["chapters"][str(n)]["text_sha256"] for n in range(10,14)})
        for id,deadline in (("P11",15),("P04",20),("P12",21)):
            self.assertEqual(state["serialization"]["promises"][id]["deadline_chapter"],deadline)
            self.assertEqual(state["serialization"]["promises"][id]["status"],"open")
        self.assertIn("正式对公账户核实收到这笔钱",body)
        self.assertIn("只是未签草案的理论空间".replace("只是","仍是"),body)
        self.assertFalse(state["serialization"]["published"])
        pre=copy.deepcopy(state);pre["revision"]=rec["base_revision"]
        pre["chapters"].pop("13");pre["tasks"]["13"]["phase"]="candidate"
        pre["serialization"]["frozen"].pop("13");pre["serialization"]["gates"]["13"]["used"]=False
        pre["serialization"]["promises"].pop("P12")
        for p in pre["serialization"]["promises"].values():
            if p.get("last_reviewed_chapter")==13:p["last_reviewed_chapter"]=12
            p["history"]=[x for x in p.get("history",[]) if x.get("chapter",0)<13]
        ns.serial_module().validate(root,pre,body,rec,report,ns.serial_api())
