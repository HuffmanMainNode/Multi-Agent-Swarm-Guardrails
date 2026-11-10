import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from masg.models import Decision
from masg.policy import PolicyError, evaluate, load_policy, load_request

ROOT = Path(__file__).resolve().parents[1]


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy(ROOT / "examples/policy.json")
        self.request = load_request(ROOT / "examples/request.json")
        self.now = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)

    def test_exact_match_allows(self):
        self.assertEqual(evaluate(self.policy, self.request, now=self.now).decision, Decision.ALLOW)

    def test_target_change_denies(self):
        self.assertEqual(evaluate(self.policy, {**self.request, "target": "secrets"}, now=self.now).decision, Decision.DENY)

    def test_review_not_allow(self):
        request = {**self.request, "action": "export", "scope": "export:external"}
        self.assertEqual(evaluate(self.policy, request, now=self.now).decision, Decision.REVIEW_REQUIRED)

    def test_explicit_deny_overrides_allow_independent_of_order(self):
        allow = self.policy["rules"][0]
        deny = {**allow, "id": "deny-same-action", "effect": "DENY"}
        for rules in ([allow, deny], [deny, allow]):
            self.assertEqual(evaluate({**self.policy, "rules": rules}, self.request, now=self.now).decision, Decision.DENY)

    def test_expired_denies(self):
        request = {**self.request, "expires_at": "2026-11-09T11:00:00Z"}
        self.assertEqual(evaluate(self.policy, request, now=self.now).reason_code, "EXPIRED")

    def test_not_yet_valid_denies(self):
        request = {**self.request, "issued_at": "2026-11-09T13:00:00Z"}
        self.assertEqual(evaluate(self.policy, request, now=self.now).reason_code, "NOT_YET_VALID")

    def test_timezone_required(self):
        request = {**self.request, "issued_at": "2026-11-09T00:00:00"}
        self.assertEqual(evaluate(self.policy, request, now=self.now).decision, Decision.DENY)

    def test_delegation_cycle_denies(self):
        request = {**self.request, "delegation_chain": ["a", "a"]}
        self.assertEqual(evaluate(self.policy, request, now=self.now).reason_code, "DELEGATION_CYCLE")

    def test_default_allow_policy_denies(self):
        self.assertEqual(evaluate({**self.policy, "default_effect": "ALLOW"}, self.request, now=self.now).decision, Decision.DENY)

    def test_naive_evaluation_clock_denies(self):
        result = evaluate(self.policy, self.request, now=datetime(2026, 11, 9, 12))
        self.assertEqual(result.reason_code, "CLOCK_INVALID")

    def test_unknown_request_field_denies(self):
        result = evaluate(self.policy, {**self.request, "admin": True}, now=self.now)
        self.assertEqual(result.decision, Decision.DENY)

    def test_unknown_policy_field_denies(self):
        result = evaluate({**self.policy, "wildcard": True}, self.request, now=self.now)
        self.assertEqual(result.decision, Decision.DENY)

    def test_malformed_rule_denies(self):
        result = evaluate({**self.policy, "rules": [{**self.policy["rules"][0], "actions": []}]}, self.request, now=self.now)
        self.assertEqual(result.decision, Decision.DENY)

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text('{"version":"one","version":"two","default_effect":"DENY","rules":[]}', encoding="utf-8")
            with self.assertRaises(PolicyError):
                load_policy(path)

    def test_nonstandard_json_constant_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text('{"version":"one","default_effect":"DENY","rules":[],"x":NaN}', encoding="utf-8")
            with self.assertRaises(PolicyError):
                load_policy(path)


if __name__ == "__main__":
    unittest.main()
