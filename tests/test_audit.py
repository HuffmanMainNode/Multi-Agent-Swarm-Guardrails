import json
import tempfile
import unittest
from pathlib import Path

from masg.audit import append_event, verify_ledger


class AuditTests(unittest.TestCase):
    def test_append_verify_and_tamper(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            append_event(path, {"decision": "DENY"})
            append_event(path, {"decision": "ALLOW"})
            self.assertTrue(verify_ledger(path)["valid"])
            rows = path.read_text().splitlines()
            item = json.loads(rows[0])
            item["event"]["decision"] = "ALLOW"
            rows[0] = json.dumps(item)
            path.write_text("\n".join(rows) + "\n")
            self.assertFalse(verify_ledger(path)["valid"])

    def test_blank_line_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            path.write_text("\n")
            self.assertFalse(verify_ledger(path)["valid"])

    def test_unhashed_extra_field_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            record = append_event(path, {"type": "test"})
            record["unhashed_metadata"] = "unexpected"
            path.write_text(json.dumps(record) + "\n")
            self.assertFalse(verify_ledger(path)["valid"])

    def test_boolean_sequence_is_not_integer_sequence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            record = append_event(path, {"type": "test"})
            record["sequence"] = True
            path.write_text(json.dumps(record) + "\n")
            self.assertFalse(verify_ledger(path)["valid"])

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            path.write_text('{"sequence":1,"sequence":1}\n')
            self.assertFalse(verify_ledger(path)["valid"])

    def test_nonstandard_numeric_value_rejected_on_append(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            with self.assertRaises(ValueError):
                append_event(path, {"value": float("nan")})


if __name__ == "__main__":
    unittest.main()
