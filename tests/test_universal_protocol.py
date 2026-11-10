"""Validate the language-neutral schemas and execute shared v1.0.0 vectors."""

import json
from datetime import datetime, timezone
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from masg.policy import evaluate, evaluate_protocol

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

    def test_reference_evaluator_matches_shared_decision_vectors(self):
        fixed_now = datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc)
        for vector in self.vectors:
            request = vector["request"]
            result = evaluate_protocol(vector["policy"], request, now=fixed_now)
            with self.subTest(vector=vector["vector_id"]):
                self.assertEqual(result.decision.value, vector["expected"]["decision"])
                self.assertEqual(result.reason_code, vector["expected"]["reason_code"])

    def test_protocol_evaluator_requires_complete_envelope(self):
        request = dict(self.vectors[0]["request"])
        request.pop("policy_version")
        result = evaluate_protocol(self.vectors[0]["policy"], request, now=datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc))
        self.assertEqual(result.reason_code, "REQUEST_INVALID")

    def test_protocol_evaluator_accepts_non_authoritative_provenance_reference(self):
        request = {**self.vectors[0]["request"], "provenance_ref": "sha256:abc123"}
        result = evaluate_protocol(self.vectors[0]["policy"], request, now=datetime(2026, 11, 10, 12, 0, 30, tzinfo=timezone.utc))
        self.assertEqual(result.decision.value, "ALLOW")

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

    def test_go_implementation_manifest_and_report_match_schemas(self):
        manifest = load_json(ROOT / "implementations/go/implementation-manifest.json")
        report = load_json(ROOT / "implementations/go/conformance-report.json")
        manifest_validator = Draft202012Validator(
            self.schemas["implementation-manifest.schema.json"],
            format_checker=FormatChecker(),
        )
        report_validator = Draft202012Validator(
            self.schemas["conformance-report.schema.json"],
            format_checker=FormatChecker(),
        )
        manifest_validator.validate(manifest)
        report_validator.validate(report)
        statuses = [item["status"] for item in report["results"]]
        expected_overall = "PASS" if all(status == "PASS" for status in statuses) else "UNKNOWN"
        self.assertEqual(report["overall_status"], expected_overall)
        self.assertTrue(report["conformance_scope"])

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


if __name__ == "__main__":
    unittest.main()
