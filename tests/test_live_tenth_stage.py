import unittest
from pathlib import Path
class StageReviewTest(unittest.TestCase):
 def test_first_ten(self):
  p=Path(__file__).resolve().parents[1]/'book'/'state.json'
  import json
  s=json.loads(p.read_text())
  self.assertEqual(len(s['chapters']),10)
  self.assertEqual(s['checkpoints'][-1]['to'],10)
