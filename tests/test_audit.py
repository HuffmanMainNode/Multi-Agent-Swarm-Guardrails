import json
import tempfile
import unittest
from pathlib import Path
from masg.audit import append_event, verify_ledger
class AuditTests(unittest.TestCase):
 def test_append_verify_and_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"ledger.jsonl"; append_event(p,{"decision":"DENY"}); append_event(p,{"decision":"ALLOW"})
   self.assertTrue(verify_ledger(p)["valid"])
   rows=p.read_text().splitlines(); item=json.loads(rows[0]); item["event"]["decision"]="ALLOW"
   rows[0]=json.dumps(item); p.write_text("\n".join(rows)+"\n")
   self.assertFalse(verify_ledger(p)["valid"])
 def test_blank_line_fails(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"ledger.jsonl"; p.write_text("\n")
   self.assertFalse(verify_ledger(p)["valid"])
if __name__=="__main__": unittest.main()
