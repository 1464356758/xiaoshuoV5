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
            # A promise due AFTER CH013 may later be fulfilled, without invalidating CH013.
            expected_action="set" if id=="P12" else "keep"
            self.assertEqual(next(p for p in report["promise_reviews"] if p["id"]==id)["action"],expected_action)
        for id in ("P04","P12"):
            self.assertEqual(state["serialization"]["promises"][id]["status"],"open")
        self.assertIn("正式对公账户核实收到这笔钱",body)
        self.assertIn("只是未签草案的理论空间".replace("只是","仍是"),body)
        self.assertFalse(state["serialization"]["published"])
        # Reconstruct the state immediately BEFORE CH013 adoption.
        # Later chapters must never make a frozen historical test fail.
        pre=copy.deepcopy(state);pre["revision"]=rec["base_revision"]
        for k in list(pre["chapters"]):
            if int(k)>=13:pre["chapters"].pop(k)
        for k in list(pre["tasks"]):
            if int(k)>13:pre["tasks"].pop(k)
        pre["tasks"]["13"]["phase"]="candidate"
        for kind in ("frozen","gates"):
            for k in list(pre["serialization"][kind]):
                if int(k)>=13:pre["serialization"][kind].pop(k)
        pre["checkpoints"]=[c for c in pre["checkpoints"] if c["to"]<13]
        # New promises introduced AFTER CH013 do not belong to its historical prestate.
        pre["serialization"]["promises"].pop("P12",None)
        for later in ("P13",):
            pre["serialization"]["promises"].pop(later,None)
        previous_reviews={p["id"]:p for p in report["promise_reviews"] if p["id"]!="P12"}
        for key,p in pre["serialization"]["promises"].items():
            if p.get("last_reviewed_chapter",0)>=13:p["last_reviewed_chapter"]=12
            p["history"]=[x for x in p.get("history",[]) if x.get("chapter",0)<13]
            if key in previous_reviews:
                p["status"]="open"
                p["deadline_chapter"]=previous_reviews[key]["deadline_chapter"]
        ns.serial_module().validate(root,pre,body,rec,report,ns.serial_api())
