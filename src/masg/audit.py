"""Single-writer local JSONL hash chain; not a signature or immutable remote log."""
import hashlib
import json
from pathlib import Path
from typing import Any

GENESIS = "0" * 64


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def append_event(path: str | Path, event: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise ValueError("event must be an object")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    previous, sequence = GENESIS, 1
    if target.exists() and target.stat().st_size:
        report = verify_ledger(target)
        if not report["valid"]:
            raise ValueError("refusing to append to invalid ledger")
        previous, sequence = report["last_hash"], report["events"] + 1
    body = {"sequence": sequence, "previous_hash": previous, "event": event}
    digest = hashlib.sha256(_canonical(body)).hexdigest()
    record = {**body, "hash": digest}
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\\n")
        stream.flush()
    return record


def verify_ledger(path: str | Path) -> dict[str, Any]:
    target, previous, count = Path(path), GENESIS, 0
    try:
        with target.open(encoding="utf-8") as stream:
            for line_no, line in enumerate(stream, 1):
                if not line.strip():
                    return {"valid": False, "events": count, "last_hash": previous, "error": f"blank line {line_no}"}
                try:
                    record = json.loads(
                        line, object_pairs_hook=_reject_pairs, parse_constant=_reject_constant,
                    )
                except (json.JSONDecodeError, ValueError):
                    return {"valid": False, "events": count, "last_hash": previous, "error": f"invalid or ambiguous JSON line {line_no}"}
                if not isinstance(record, dict) or set(record) != {"sequence", "previous_hash", "event", "hash"}:
                    return {"valid": False, "events": count, "last_hash": previous, "error": f"unexpected record shape line {line_no}"}
                if type(record.get("sequence")) is not int or record["sequence"] != count + 1:
                    return {"valid": False, "events": count, "last_hash": previous, "error": f"invalid sequence line {line_no}"}
                if record.get("previous_hash") != previous:
                    return {"valid": False, "events": count, "last_hash": previous, "error": f"sequence/link mismatch line {line_no}"}
                if not isinstance(record.get("event"), dict):
                    return {"valid": False, "events": count, "last_hash": previous, "error": f"invalid event line {line_no}"}
                if not isinstance(record.get("hash"), str) or len(record["hash"]) != 64:
                    return {"valid": False, "events": count, "last_hash": previous, "error": f"invalid hash field line {line_no}"}
                body = {"sequence": record["sequence"], "previous_hash": record["previous_hash"], "event": record["event"]}
                digest = hashlib.sha256(_canonical(body)).hexdigest()
                if record["hash"] != digest:
                    return {"valid": False, "events": count, "last_hash": previous, "error": f"hash mismatch line {line_no}"}
                previous, count = digest, count + 1
    except (OSError, UnicodeDecodeError):
        return {"valid": False, "events": count, "last_hash": previous, "error": "ledger cannot be read as UTF-8"}
    return {"valid": True, "events": count, "last_hash": previous, "error": None}
