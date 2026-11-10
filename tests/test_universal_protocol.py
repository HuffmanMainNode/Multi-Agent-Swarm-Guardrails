"""Validate the language-neutral schemas and execute shared v1.0.0 vectors."""

import json
from datetime import datetime, timezone
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from masg.policy import PolicyError, _check_json_depth, evaluate, evaluate_protocol, evaluate_protocol_json

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
VECTOR_FILE = ROOT / "vectors/v1.0.0/decision-vectors.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_schemas():
    schemas = {path.name: load_json(path) for path in SCHEMA_DIR.glob("*.schema.json")}
    registry = Registry()
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return schemas, registry


class UniversalProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas, cls.registry = load_schemas()
        cls.vectors = load_json(VECTOR_FILE)
        cls.parser_vectors = load_json(ROOT / "vectors/v1.0.0/parser-negative-vectors.json")
        cls.vector_validator = Draft202012Validator(
            cls.schemas["conformance-vector.schema.json"],
            registry=cls.registry,
            format_checker=FormatChecker(),
        )

    def test_all_schemas_are_valid_draft_2020_12(self):
        self.assertGreaterEqual(len(self.schemas), 6)

    def test_all_portable_vectors_match_their_schema(self):
        self.assertGreaterEqual(len(self.vectors), 8)
        for vector in self.vectors:
            with self.subTest(vector=vector.get("vector_id")):
                self.vector_validator.validate(vector)

    def test_shared_parser_negative_vectors_match_their_schema(self):
        schema = self.schemas["parser-negative-vector.schema.json"]
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertGreaterEqual(len(self.parser_vectors), 18)
        for fixture in self.parser_vectors:
            with self.subTest(fixture=fixture["fixture_id"]):
                validator.validate(fixture)

    def test_python_parser_matches_shared_negative_vectors(self):
        for fixture in self.parser_vectors:
            result = evaluate_protocol_json(
                bytes.fromhex(fixture["policy_json_hex"]),
                bytes.fromhex(fixture["request_json_hex"]),
                now=datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc),
            )
            with self.subTest(fixture=fixture["fixture_id"]):
                self.assertEqual(result.reason_code, fixture["expected_reason_code"])

    def test_reference_evaluator_matches_shared_decision_vectors(self):
        fixed_now = datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc)
        for vector in self.vectors:
            request = vector["request"]
            result = evaluate_protocol(vector["policy"], request, now=fixed_now)
            with self.subTest(vector=vector["vector_id"]):
                self.assertEqual(result.decision.value, vector["expected"]["decision"])
                self.assertEqual(result.reason_code, vector["expected"]["reason_code"])

    def test_json_depth_boundary_is_exactly_32_containers(self):
        _check_json_depth(b"[" * 32 + b"0" + b"]" * 32)
        with self.assertRaises(PolicyError):
            _check_json_depth(b"[" * 33 + b"0" + b"]" * 33)

    def test_strict_json_protocol_entrypoint_accepts_valid_envelope(self):
        vector = self.vectors[0]
        result = evaluate_protocol_json(
            json.dumps(vector["policy"]).encode("utf-8"),
            json.dumps(vector["request"]).encode("utf-8"),
            now=datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(result.decision.value, "ALLOW")

    def test_strict_json_protocol_entrypoint_rejects_duplicate_keys(self):
        policy_json = b'{"version":"p1","default_effect":"DENY","rules":[]}'
        request_json = b'{"protocol_version":"1.0.0","protocol_version":"1.0.0"}'
        result = evaluate_protocol_json(
            policy_json, request_json,
            now=datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(result.reason_code, "REQUEST_INVALID")

    def test_strict_json_protocol_entrypoint_rejects_depth_utf8_and_size(self):
        policy_json = b'{"version":"p1","default_effect":"DENY","rules":[]}'
        now = datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc)
        nested = b'{"x":' + (b"[" * 33) + b"0" + (b"]" * 33) + b"}"
        self.assertEqual(evaluate_protocol_json(policy_json, nested, now=now).reason_code, "REQUEST_INVALID")
        self.assertEqual(evaluate_protocol_json(policy_json, b"\\xff", now=now).reason_code, "REQUEST_INVALID")
        self.assertEqual(evaluate_protocol_json(policy_json, b" " * 65537, now=now).reason_code, "REQUEST_INVALID")

    def test_protocol_evaluator_requires_complete_envelope(self):
        request = dict(self.vectors[0]["request"])
        request.pop("policy_version")
        result = evaluate_protocol(self.vectors[0]["policy"], request, now=datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc))
        self.assertEqual(result.reason_code, "REQUEST_INVALID")

    def test_protocol_evaluator_accepts_non_authoritative_provenance_reference(self):
        request = {**self.vectors[0]["request"], "provenance_ref": "sha256:abc123"}
        result = evaluate_protocol(self.vectors[0]["policy"], request, now=datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc))
        self.assertEqual(result.decision.value, "ALLOW")

    def test_schema_rejects_unknown_offset_and_excess_precision(self):
        schema = self.schemas["decision-request.schema.json"]
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        valid = dict(self.vectors[0]["request"])
        valid["issued_at"] = "2026-11-10T12:00:00.123456Z"
        self.assertTrue(validator.is_valid(valid))
        valid["issued_at"] = "2026-11-10T12:00:00.1234567Z"
        self.assertFalse(validator.is_valid(valid))
        valid["issued_at"] = "2026-11-10T12:00:00-00:00"
        self.assertFalse(validator.is_valid(valid))

    def test_protocol_timestamp_precision_is_bounded(self):
        request = {**self.vectors[0]["request"], "issued_at": "2026-11-10T12:00:00.1234567Z"}
        result = evaluate_protocol(self.vectors[0]["policy"], request, now=datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc))
        self.assertEqual(result.reason_code, "REQUEST_INVALID")
        request["issued_at"] = "2026-11-10T12:00:00-00:00"
        result = evaluate_protocol(self.vectors[0]["policy"], request, now=datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc))
        self.assertEqual(result.reason_code, "REQUEST_INVALID")

    def test_protocol_envelopes_reject_unknown_fields(self):
        schema = self.schemas["decision-request.schema.json"]
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        valid = self.vectors[0]["request"]
        invalid = {**valid, "unreviewed_security_field": True}
        self.assertTrue(validator.is_valid(valid))
        self.assertFalse(validator.is_valid(invalid))

    def test_all_reference_implementation_manifests_and_reports_match_schemas(self):
        manifest_validator = Draft202012Validator(
            self.schemas["implementation-manifest.schema.json"],
            format_checker=FormatChecker(),
        )
        report_validator = Draft202012Validator(
            self.schemas["conformance-report.schema.json"],
            format_checker=FormatChecker(),
        )
        for language in ("go", "rust", "javascript"):
            with self.subTest(language=language):
                manifest = load_json(ROOT / f"implementations/{language}/implementation-manifest.json")
                report = load_json(ROOT / f"implementations/{language}/conformance-report.json")
                manifest_validator.validate(manifest)
                report_validator.validate(report)
                self.assertEqual(manifest["implementation_id"], report["implementation_id"])
                self.assertEqual(manifest["version"], report["implementation_version"])
                self.assertEqual(manifest["protocol_versions"], [report["protocol_version"]])
                statuses = [item["status"] for item in report["results"]]
                expected_overall = "PASS" if all(status == "PASS" for status in statuses) else "UNKNOWN"
                self.assertEqual(report["overall_status"], expected_overall)
                if language == "javascript":
                    self.assertEqual(report["conformance_scope"], "portable_policy_time_and_parser_negative_vectors_only")
                    self.assertEqual(len(report["results"]), len(self.vectors) + len(self.parser_vectors))
                else:
                    self.assertEqual(report["conformance_scope"], "portable_policy_decision_and_time_vectors_only")
                    self.assertEqual(len(report["results"]), len(self.vectors))
                if report["overall_status"] == "PASS":
                    self.assertRegex(report["source_revision"], r"^[0-9a-f]{40}$")
                    self.assertTrue(all(item.get("evidence_ref", "").startswith("https://github.com/") for item in report["results"]))
                else:
                    self.assertTrue(all(status == "NOT_TESTED" for status in statuses))
                self.assertTrue(manifest["limitations"])
                self.assertTrue(report["limitations"])
                self.assertTrue(all(item["status"] == "NOT_TESTED" for item in manifest["contract_status"]))

    def test_controlled_core_glossary_matches_schema_and_has_unique_ids(self):
        schema = self.schemas["core-glossary.schema.json"]
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        glossary = load_json(ROOT / "localization/glossary/core-concepts.json")
        validator.validate(glossary)
        concept_ids = [item["concept_id"] for item in glossary["concepts"]]
        self.assertEqual(len(concept_ids), len(set(concept_ids)))
        self.assertEqual(glossary["source_locale"], "en")

    def test_localization_source_and_untranslated_template_match_schema(self):
        schema = self.schemas["translation-pack.schema.json"]
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        source = load_json(ROOT / "localization/locales/en/messages.json")
        template = load_json(ROOT / "localization/locales/es/messages.template.json")
        validator.validate(source)
        validator.validate(template)
        self.assertEqual(source["locale"], source["source_locale"])
        self.assertTrue(all(item["status"] == "SOURCE" for item in source["messages"].values()))
        self.assertTrue(all(item["status"] == "UNTRANSLATED" and item["text"] == "" for item in template["messages"].values()))

        reviewed = dict(template)
        reviewed["messages"] = dict(template["messages"])
        first_id = next(iter(reviewed["messages"]))
        reviewed["messages"][first_id] = {
            "text": "Texto revisado",
            "status": "HUMAN_REVIEWED",
            "review": {"reviewer": "community-reviewer", "reviewed_at": "2026-11-10T05:00:00Z"},
        }
        validator.validate(reviewed)
        reviewed["messages"][first_id].pop("review")
        self.assertFalse(validator.is_valid(reviewed))

    def test_semantic_frame_schema_requires_evidence_for_verified_claims(self):
        schema = self.schemas["semantic-frame.schema.json"]
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        frame = load_json(ROOT / "examples/semantic-frame.example.json")
        validator.validate(frame)
        invalid = json.loads(json.dumps(frame))
        invalid["claims"][0].pop("evidence_refs")
        self.assertFalse(validator.is_valid(invalid))

    def test_example_extension_manifest_matches_schema(self):
        manifest = load_json(
            ROOT / "extensions/examples/generic-tool-action/manifest.json"
        )
        validator = Draft202012Validator(
            self.schemas["extension-manifest.schema.json"],
            format_checker=FormatChecker(),
        )
        validator.validate(manifest)
        self.assertTrue(manifest["security_critical"])
        self.assertGreaterEqual(len(manifest["limitations"]), 1)

    def test_response_schema_accepts_standard_decision(self):
        response = {
            "protocol_version": "1.0.0",
            "message_type": "authorization_response",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "decision": "DENY",
            "reason_code": "EXPLICIT_DENY",
            "evaluated_at": "2026-11-10T12:00:30Z",
            "policy_version": "vector-policy-1",
        }
        validator = Draft202012Validator(
            self.schemas["decision-response.schema.json"],
            format_checker=FormatChecker(),
        )
        validator.validate(response)

    def test_uefp_participant_manifest_example_matches_schema(self):
        schema = self.schemas["participant-manifest.schema.json"]
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        manifest = load_json(ROOT / "examples/participant-manifest.example.json")
        validator.validate(manifest)
        self.assertTrue(manifest["consent"]["requires_explicit_exchange_acceptance"])
        self.assertTrue(manifest["limitations"])

    def test_uefp_participant_manifest_rejects_unsafe_or_ambiguous_shapes(self):
        schema = self.schemas["participant-manifest.schema.json"]
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        valid = load_json(ROOT / "examples/participant-manifest.example.json")
        cases = []
        missing_consent = json.loads(json.dumps(valid))
        missing_consent.pop("consent")
        cases.append(("missing consent", missing_consent))
        implicit_consent = json.loads(json.dumps(valid))
        implicit_consent["consent"]["requires_explicit_exchange_acceptance"] = False
        cases.append(("implicit exchange acceptance", implicit_consent))
        unknown_type = json.loads(json.dumps(valid))
        unknown_type["participant_type"] = "AUTONOMOUS_AUTHORITY"
        cases.append(("unknown participant type", unknown_type))
        duplicate_versions = json.loads(json.dumps(valid))
        duplicate_versions["protocol_versions"].append(duplicate_versions["protocol_versions"][0])
        cases.append(("duplicate protocol version", duplicate_versions))
        malformed_id = json.loads(json.dumps(valid))
        malformed_id["participant_id"] = "../other-participant"
        cases.append(("path-like participant id", malformed_id))
        undeclared_property = json.loads(json.dumps(valid))
        undeclared_property["verified"] = True
        cases.append(("unsupported verification claim", undeclared_property))
        for label, candidate in cases:
            with self.subTest(case=label):
                self.assertFalse(validator.is_valid(candidate))

    def test_uefp_handshake_messages_match_schema_and_reject_unknown_types(self):
        schema = self.schemas["uefp-handshake-message.schema.json"]
        validator = Draft202012Validator(schema, registry=self.registry, format_checker=FormatChecker())
        manifest = load_json(ROOT / "examples/participant-manifest.example.json")
        common = {
            "protocol_version": "0.1.0",
            "session_id": "session-2026-001",
            "message_id": "message-001",
            "sender_id": "community.lab",
            "recipient_id": "agent.example",
        }
        valid_messages = [
            {**common, "message_type": "INTRODUCE", "payload": {"manifest": manifest}},
            {**common, "message_type": "RESPONSE", "payload": {"manifest": manifest}},
            {**common, "message_type": "PROPOSE", "payload": {
                "proposal_id": "proposal-1", "topic": "Compare local learning methods",
                "data_scope": "Public documentation only", "format": "application/json",
                "retention": "Do not retain beyond this exchange", "intended_use": "Community learning",
                "license": "CC-BY-4.0", "provenance": "Contributor-authored public material"
            }},
            {**common, "message_type": "ACCEPT", "payload": {"proposal_id": "proposal-1"}},
            {**common, "message_type": "DECLINE", "payload": {"proposal_id": "proposal-1"}},
            {**common, "message_type": "EXCHANGE", "payload": {
                "proposal_id": "proposal-1", "content_format": "text/plain", "content": "Example exchange"
            }},
            {**common, "message_type": "CLOSE", "payload": {"reason": "COMPLETED"}},
        ]
        for message in valid_messages:
            with self.subTest(message_type=message["message_type"]):
                validator.validate(message)
        invalid = {**common, "message_type": "EXECUTE", "payload": {}}
        self.assertFalse(validator.is_valid(invalid))
        invalid = {**common, "message_type": "ACCEPT", "payload": {"proposal_id": "proposal-1", "approved": True}}
        self.assertFalse(validator.is_valid(invalid))
        invalid = {**common, "message_type": "EXCHANGE", "payload": {
            "proposal_id": "proposal-1", "content_format": "text/plain"
        }}
        self.assertFalse(validator.is_valid(invalid))
        invalid = {**common, "message_type": "INTRODUCE", "payload": {
            "manifest": {**manifest, "consent": {
                "default_data_sharing": "PUBLIC_ONLY",
                "requires_explicit_exchange_acceptance": False
            }}
        }}
        self.assertFalse(validator.is_valid(invalid))


if __name__ == "__main__":
    unittest.main()
