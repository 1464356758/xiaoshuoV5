import copy, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import novel_state as ns
class RealSecondReleaseTest(unittest.TestCase):
 def test_release_and_provenance(self):
  book=ROOT/"book"
  st=ns.load_state(book);ns.verify_files(book,st)
  self.assertEqual(len(st["chapters"]),2)
  item=st["chapters"]["2"]
  body=(book/item["text_path"]).read_text(encoding="utf-8")
  record=ns.read_json(book/item["record_path"])
  gate=st["serialization"]["gates"]["2"]
  report=ns.read_json(book/gate["path"])
  self.assertEqual(ns.han_count(body),9418)
  self.assertEqual(ns.digest(body),item["text_sha256"])
  self.assertEqual(ns.digest(json.dumps(report,ensure_ascii=False,indent=2)+"\n"),gate["sha256"])
  self.assertEqual(st["serialization"]["promises"]["P01A"]["status"],"closed")
  self.assertEqual(len(st["serialization"]["published"]),0)
  old=copy.deepcopy(st)
  del old["chapters"]["2"]
  old["revision"]=record["base_revision"]
  old["tasks"]["2"]["phase"]="candidate"
  old["serialization"]["frozen"].pop("2")
  old["serialization"]["gates"]["2"]["used"]=False
  ns.serial_module().validate(book,old,body,record,report,ns.serial_api())
if __name__=="__main__":unittest.main()
