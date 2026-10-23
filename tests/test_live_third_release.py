import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import novel_state as ns


class RealThirdReleaseTest(unittest.TestCase):
    def test_ch003_full_gate_and_ledger(self):
        book = ROOT / "book"
        state = ns.load_state(book)
        ns.verify_files(book, state)
        self.assertGreaterEqual(len(state["chapters"]), 3)
        chapter = state["chapters"]["3"]
        content = (book / chapter["text_path"]).read_text(encoding="utf-8")
        record = ns.read_json(book / chapter["record_path"])
        gate = state["serialization"]["gates"]["3"]
        report = ns.read_json(book / gate["path"])
        self.assertEqual(ns.han_count(content), 9654)
        self.assertEqual(ns.digest(content), chapter["text_sha256"])
        self.assertEqual(
            ns.digest(json.dumps(report, ensure_ascii=False, indent=2) + "\n"), gate["sha256"]
        )
        self.assertEqual(state["serialization"]["promises"]["P08"]["deadline_chapter"], 100)
        self.assertEqual(state["serialization"]["promises"]["P01A"]["status"], "closed")
        self.assertFalse(state["serialization"]["published"])
        before = copy.deepcopy(state)
        before["chapters"] = {
            k: v for k, v in before["chapters"].items() if int(k) <= 2
        }
        before["revision"] = record["base_revision"]
        before["tasks"]["3"]["phase"] = "candidate"
        before["serialization"]["frozen"].pop("3")
        before["serialization"]["gates"]["3"]["used"] = False
        before["serialization"]["promises"].pop("P08")
        ns.serial_module().validate(
            book, before, content, record, report, ns.serial_api()
        )


if __name__ == "__main__":
    unittest.main()
