import unittest
from pathlib import Path
class StageReviewTest(unittest.TestCase):
 def test_first_ten(self):
  p=Path(__file__).resolve().parents[1]/'book'/'state.json'
  import json
  s=json.loads(p.read_text(encoding='utf-8'))
  self.assertGreaterEqual(len(s['chapters']),10)
  self.assertIn('10',s['chapters'])
  self.assertTrue(any(c['kind']=='stage' and c['from']==1 and c['to']==10 and c['decision'] in ('continue','adjust_future') for c in s['checkpoints']))
