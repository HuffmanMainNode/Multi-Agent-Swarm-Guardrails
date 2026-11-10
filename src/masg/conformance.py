"""Repository artifact and contract-catalog checks only; not deployment certification."""
import json
from pathlib import Path
import re

REQUIRED = [f"MSC-{index:03d}" for index in range(1, 11)]
FILES = [
    "README.md", "SECURITY.md", "LICENSE", "contracts/manifest.json",
    "contracts/schema/contract.schema.json", "docs/THREAT_MODEL.md",
    "docs/CONFORMANCE.md", "pyproject.toml",
]
CATALOG_KEYS = {"catalog_name", "catalog_version", "status", "maintainer", "contracts"}
CONTRACT_KEYS = {"id", "title", "version", "status", "requirement", "failure", "evidence"}
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
MAX_MANIFEST_BYTES = 262_144


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: Path):
    raw = path.read_bytes()
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError("JSON artifact exceeds size limit")
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid constant {value}")),
    )


def verify_repository(root: str | Path) -> dict:
    base, errors, warnings, found = Path(root), [], [], []
    for item in FILES:
        if not (base / item).is_file():
            errors.append(f"missing required file: {item}")

    manifest_path = base / "contracts/manifest.json"
    if manifest_path.is_file():
        try:
            data = _read_json(manifest_path)
            if not isinstance(data, dict) or set(data) != CATALOG_KEYS:
                errors.append("contract catalog has invalid top-level shape")
            else:
                entries = data.get("contracts")
                if not isinstance(entries, list) or len(entries) > 100:
                    errors.append("contracts must be an array of at most 100 entries")
                else:
                    seen = []
                    for index, entry in enumerate(entries):
                        if not isinstance(entry, dict) or set(entry) != CONTRACT_KEYS:
                            errors.append(f"contracts[{index}] has invalid shape")
                            continue
                        identifier = entry.get("id")
                        if not isinstance(identifier, str):
                            errors.append(f"contracts[{index}].id must be a string")
                        else:
                            seen.append(identifier)
                        if not isinstance(entry.get("title"), str) or not entry["title"].strip():
                            errors.append(f"contracts[{index}].title is invalid")
                        if not isinstance(entry.get("version"), str) or not VERSION.fullmatch(entry["version"]):
                            errors.append(f"contracts[{index}].version is invalid")
                        if entry.get("status") not in {"specified", "partially_implemented", "implemented", "deprecated"}:
                            errors.append(f"contracts[{index}].status is invalid")
                        if not isinstance(entry.get("requirement"), str) or len(entry["requirement"]) < 20:
                            errors.append(f"contracts[{index}].requirement is too short or invalid")
                        if not isinstance(entry.get("failure"), str) or not entry["failure"].strip():
                            errors.append(f"contracts[{index}].failure is invalid")
                        evidence = entry.get("evidence")
                        if not isinstance(evidence, list) or not evidence or not all(isinstance(x, str) and x.strip() for x in evidence):
                            errors.append(f"contracts[{index}].evidence must be a non-empty string array")
                    found = seen
                    missing = sorted(set(REQUIRED) - set(seen))
                    unexpected = sorted(set(seen) - set(REQUIRED))
                    duplicates = sorted({item for item in seen if seen.count(item) > 1})
                    if missing:
                        errors.append("missing IDs: " + ", ".join(missing))
                    if unexpected:
                        errors.append("unexpected IDs: " + ", ".join(unexpected))
                    if duplicates:
                        errors.append("duplicate IDs: " + ", ".join(duplicates))
                if data.get("catalog_version") != "1.0.0":
                    warnings.append("catalog version differs from baseline")
                if data.get("status") != "experimental":
                    warnings.append("catalog status is not experimental; verify assurance claims")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"cannot validate manifest: {exc}")

    schema_path = base / "contracts/schema/contract.schema.json"
    if schema_path.is_file():
        try:
            schema = _read_json(schema_path)
            if not isinstance(schema, dict) or schema.get("type") != "object" or schema.get("additionalProperties") is not False:
                errors.append("contract schema must be an object schema with additionalProperties=false")
            else:
                required_fields = schema.get("required")
                if not isinstance(required_fields, list) or not all(isinstance(x, str) for x in required_fields):
                    errors.append("contract schema required field list is invalid")
                elif not CONTRACT_KEYS.issubset(set(required_fields)):
                    errors.append("contract schema required fields do not cover the contract catalog")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"cannot validate contract schema: {exc}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "scope": "repository_structure_and_contract_catalog",
        "contracts_found": len(found),
        "contracts_required": len(REQUIRED),
        "errors": errors,
        "warnings": warnings,
        "limitations": [
            "Does not test live deployment or enforcement mediation.",
            "Does not authenticate identities or verify policy signatures.",
            "Does not prove OS isolation, complete path coverage, or safety.",
            "Does not execute every JSON Schema keyword or certify deployment manifests.",
        ],
    }
