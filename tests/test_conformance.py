import json
import tempfile
import unittest
from pathlib import Path

from masg.conformance import verify_repository

ROOT = Path(__file__).resolve().parents[1]


class ConformanceTests(unittest.TestCase):
    def _fixture(self, root):
        for name in ["README.md", "SECURITY.md", "LICENSE", "docs/THREAT_MODEL.md", "docs/CONFORMANCE.md", "pyproject.toml"]:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("placeholder", encoding="utf-8")
        schema = root / "contracts/schema/contract.schema.json"
        schema.parent.mkdir(parents=True, exist_ok=True)
        schema.write_text(json.dumps({
            "type": "object", "additionalProperties": False,
            "required": ["id", "title", "version", "status", "requirement", "failure", "evidence"],
        }), encoding="utf-8")
        source = json.loads((ROOT / "contracts/manifest.json").read_text(encoding="utf-8"))
        return root, source

    def test_catalog_has_ten_contracts(self):
        result = verify_repository(ROOT)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["contracts_found"], 10)
        self.assertEqual(result["scope"], "repository_structure_and_contract_catalog")

    def test_duplicate_contract_id_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root, source = self._fixture(Path(directory))
            source["contracts"][1]["id"] = source["contracts"][0]["id"]
            manifest = root / "contracts/manifest.json"
            manifest.write_text(json.dumps(source), encoding="utf-8")
            result = verify_repository(root)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("duplicate IDs" in error for error in result["errors"]))

    def test_extra_contract_field_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root, source = self._fixture(Path(directory))
            source["contracts"][0]["unexpected"] = "untrusted"
            (root / "contracts/manifest.json").write_text(json.dumps(source), encoding="utf-8")
            result = verify_repository(root)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("invalid shape" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
