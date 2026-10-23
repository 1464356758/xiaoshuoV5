import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import novel_state as ns


class LiveFirstChapterReleaseTest(unittest.TestCase):
    def test_ch001_gate_against_script(self):
        book = ROOT / "book"
        state = ns.read_json(book / "state.json")
        ns.verify_files(book, state)
        self.assertEqual(state["book_id"], "fecf168c-8f57-4c2c-98ad-622f20134a1d")
        c = state["chapters"]["1"]
        self.assertEqual(c["han_count"], 9751)
        text = (book / c["text_path"]).read_text(encoding="utf-8")
        record = ns.read_json(book / c["record_path"])
        report = ns.read_json(book / state["serialization"]["gates"]["1"]["path"])
        self.assertEqual(ns.han_count(text), 9751)
        self.assertEqual(ns.digest(text), c["text_sha256"])
        self.assertEqual(ns.digest(json.dumps(report, ensure_ascii=False, indent=2) + "\n"),
                         state["serialization"]["gates"]["1"]["sha256"])
        self.assertTrue(state["serialization"]["frozen"]["1"])
        pre = copy.deepcopy(state)
        pre["chapters"] = {}
        pre["revision"] = record["base_revision"]
        pre["tasks"]["1"]["phase"] = "candidate"
        pre["serialization"]["frozen"] = {}
        pre["serialization"]["promises"] = {}
        pre["serialization"]["gates"]["1"]["used"] = False
        ns.serial_module().validate(book, pre, text, record, report, ns.serial_api())


if __name__ == "__main__":
    unittest.main()
