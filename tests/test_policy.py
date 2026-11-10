import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from masg.models import Decision
from masg.policy import PolicyError, evaluate, evaluate_protocol_json, load_policy, load_request

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

    def test_policy_rule_id_is_required(self):
        policy = {**self.policy, "rules": [{key: value for key, value in self.policy["rules"][0].items() if key != "id"}]}
        self.assertEqual(evaluate(policy, self.request, now=self.now).reason_code, "POLICY_INVALID")

    def test_policy_rule_limit_matches_protocol_schema(self):
        rules = [self.policy["rules"][0]] * 1001
        self.assertEqual(evaluate({**self.policy, "rules": rules}, self.request, now=self.now).reason_code, "POLICY_INVALID")

    def test_action_selector_limit_matches_protocol_schema(self):
        rule = {**self.policy["rules"][0], "actions": ["x" * 257]}
        self.assertEqual(evaluate({**self.policy, "rules": [rule]}, self.request, now=self.now).reason_code, "POLICY_INVALID")

    def test_unicode_selector_limit_counts_characters(self):
        rule = {**self.policy["rules"][0], "principals": ["é" * 1024]}
        self.assertEqual(evaluate({**self.policy, "rules": [rule]}, self.request, now=self.now).reason_code, "NO_MATCH")
        rule["principals"] = ["é" * 1025]
        self.assertEqual(evaluate({**self.policy, "rules": [rule]}, self.request, now=self.now).reason_code, "POLICY_INVALID")

    def test_nonstandard_json_constant_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text('{"version":"one","default_effect":"DENY","rules":[],"x":NaN}', encoding="utf-8")
            with self.assertRaises(PolicyError):
                load_policy(path)



    def test_all_shared_parser_negative_vectors_fail_closed(self):
        fixtures_path = ROOT / "vectors/v1.0.0/parser-negative-vectors.json"
        fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
        self.assertEqual(len(fixtures), 21)
        for fixture in fixtures:
            result = evaluate_protocol_json(
                bytes.fromhex(fixture["policy_json_hex"]),
                bytes.fromhex(fixture["request_json_hex"]),
                now=self.now,
            )
            self.assertEqual(result.decision, Decision.DENY, fixture["fixture_id"])
            self.assertEqual(
                result.reason_code, fixture["expected_reason_code"], fixture["fixture_id"]
            )

    def test_protocol_rejects_null_optional_provenance_reference(self):
        policy = {
            "version": "p1", "default_effect": "DENY",
            "rules": [{
                "id": "allow-read", "principals": ["agent:reader"],
                "actions": ["read"], "targets": ["reports:weekly"],
                "scopes": ["summary"], "effect": "ALLOW",
            }],
        }
        request = {
            "protocol_version": "1.0.0", "message_type": "authorization_request",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "issued_at": "2026-11-10T12:00:00Z", "expires_at": "2026-11-10T12:01:00Z",
            "principal": "agent:reader", "action": "read", "target": "reports:weekly",
            "scope": "summary", "policy_version": "p1", "provenance_ref": None,
        }
        result = evaluate_protocol_json(
            json.dumps(policy).encode(), json.dumps(request).encode(), now=self.now
        )
        self.assertEqual(result.reason_code, "REQUEST_INVALID")

    def test_protocol_rejects_unpaired_surrogates_in_policy_and_request(self):
        policy = {
            "version": "p1", "default_effect": "DENY",
            "rules": [{
                "id": "allow-read", "principals": ["agent:\ud800"],
                "actions": ["read"], "targets": ["reports:weekly"],
                "scopes": ["summary"], "effect": "ALLOW",
            }],
        }
        request = {
            "protocol_version": "1.0.0", "message_type": "authorization_request",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "issued_at": "2026-11-10T12:00:00Z", "expires_at": "2026-11-10T12:01:00Z",
            "principal": "agent:reader", "action": "read", "target": "reports:weekly",
            "scope": "summary", "policy_version": "p1",
        }
        result = evaluate_protocol_json(
            json.dumps(policy).encode(), json.dumps(request).encode(), now=self.now
        )
        self.assertEqual(result.reason_code, "POLICY_INVALID")

        policy["rules"][0]["principals"] = ["agent:reader"]
        request["principal"] = "agent:\ud800"
        result = evaluate_protocol_json(
            json.dumps(policy).encode(), json.dumps(request).encode(), now=self.now
        )
        self.assertEqual(result.reason_code, "REQUEST_INVALID")


if __name__ == "__main__":
    unittest.main()
