import unittest
from datetime import datetime, timezone
from pathlib import Path
from masg.policy import evaluate, load_policy, load_request
from masg.models import Decision
ROOT=Path(__file__).resolve().parents[1]
class PolicyTests(unittest.TestCase):
 def setUp(self):
  self.policy=load_policy(ROOT/"examples/policy.json"); self.request=load_request(ROOT/"examples/request.json")
  self.now=datetime(2026,11,9,12,tzinfo=timezone.utc)
 def test_exact_match_allows(self):
  self.assertEqual(evaluate(self.policy,self.request,now=self.now).decision,Decision.ALLOW)
 def test_target_change_denies(self):
  self.assertEqual(evaluate(self.policy,{**self.request,"target":"secrets"},now=self.now).decision,Decision.DENY)
 def test_review_not_allow(self):
  r={**self.request,"action":"export","scope":"export:external"}
  self.assertEqual(evaluate(self.policy,r,now=self.now).decision,Decision.REVIEW_REQUIRED)
 def test_expired_denies(self):
  r={**self.request,"expires_at":"2026-11-09T11:00:00Z"}
  self.assertEqual(evaluate(self.policy,r,now=self.now).reason_code,"EXPIRED")
 def test_not_yet_valid_denies(self):
  r={**self.request,"issued_at":"2026-11-09T13:00:00Z"}
  self.assertEqual(evaluate(self.policy,r,now=self.now).reason_code,"NOT_YET_VALID")
 def test_timezone_required(self):
  r={**self.request,"issued_at":"2026-11-09T00:00:00"}
  self.assertEqual(evaluate(self.policy,r,now=self.now).decision,Decision.DENY)
 def test_delegation_cycle_denies(self):
  r={**self.request,"delegation_chain":["a","a"]}
  self.assertEqual(evaluate(self.policy,r,now=self.now).reason_code,"DELEGATION_CYCLE")
 def test_default_allow_policy_denies(self):
  self.assertEqual(evaluate({**self.policy,"default_effect":"ALLOW"},self.request,now=self.now).decision,Decision.DENY)
if __name__=="__main__": unittest.main()
