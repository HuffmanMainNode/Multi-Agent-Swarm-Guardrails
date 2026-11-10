"""Strict, deny-by-default local policy evaluation.

This module evaluates policy data. It does not authenticate principals, protect policy
provenance, mediate operating-system side effects, or provide a sandbox.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from .models import Decision, Evaluation
from .replay import ReplayStore, ReplayStoreError

MAX_POLICY_BYTES = 1_048_576
MAX_REQUEST_BYTES = 65_536
MAX_JSON_DEPTH = 32


def _check_json_depth(raw: bytes) -> None:
    depth = 0
    in_string = False
    escaped = False
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
        elif byte == 0x22:
            in_string = True
        elif byte in (0x7B, 0x5B):
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise PolicyError("JSON nesting exceeds the protocol limit")
        elif byte in (0x7D, 0x5D):
            depth -= 1


MAX_RULES = 1_000
MAX_SELECTORS = 128
MAX_TEXT_LENGTH = 1_024
SELECTOR_MAX_LENGTH = {"principals": 1_024, "actions": 256, "targets": 512, "scopes": 512}
POLICY_VERSION_MAX_LENGTH = 128
POLICY_KEYS = {"version", "default_effect", "rules"}
RULE_KEYS = {"id", "principals", "actions", "targets", "scopes", "effect"}
REQUEST_KEYS = {
    "principal", "action", "target", "scope", "request_id",
    "issued_at", "expires_at", "delegation_chain", "policy_version",
}
RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$"
)


class PolicyError(ValueError):
    """Raised when policy or request input is invalid."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PolicyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise PolicyError(f"non-standard JSON numeric constant: {value}")


def _reject_surrogates(value: Any) -> None:
    """Reject escaped unpaired UTF-16 surrogates; protocol strings are Unicode scalar values."""
    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise PolicyError("JSON contains an unpaired Unicode surrogate")
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_surrogates(key)
            _reject_surrogates(item)
    elif isinstance(value, list):
        for item in value:
            _reject_surrogates(item)


def _load(path: str | Path, *, max_bytes: int) -> dict[str, Any]:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise PolicyError(f"cannot read input: {exc}") from exc
    if len(raw) > max_bytes:
        raise PolicyError(f"input exceeds {max_bytes} byte limit")
    _check_json_depth(raw)
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PolicyError(f"invalid UTF-8 JSON: {exc}") from exc
    _reject_surrogates(value)
    if not isinstance(value, dict):
        raise PolicyError("top-level JSON must be an object")
    return value


def _text(value: Any, field: str, *, max_length: int = MAX_TEXT_LENGTH) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= max_length


def _selector_list(value: Any, field: str) -> bool:
    max_length = SELECTOR_MAX_LENGTH[field]
    return (
        isinstance(value, list)
        and 1 <= len(value) <= MAX_SELECTORS
        and all(_text(item, field, max_length=max_length) for item in value)
        and len(value) == len(set(value))
    )


def load_policy(path: str | Path) -> dict[str, Any]:
    policy = _load(path, max_bytes=MAX_POLICY_BYTES)
    if set(policy) != POLICY_KEYS:
        raise PolicyError("policy must contain exactly version, default_effect, and rules")
    if not _text(policy.get("version"), "version", max_length=POLICY_VERSION_MAX_LENGTH):
        raise PolicyError("policy.version must be a non-empty string of at most 128 characters")
    if policy.get("default_effect") != "DENY":
        raise PolicyError("default_effect must be DENY")
    rules = policy.get("rules")
    if not isinstance(rules, list) or len(rules) > MAX_RULES:
        raise PolicyError(f"policy.rules must be an array of at most {MAX_RULES} rules")
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict) or set(rule) != RULE_KEYS:
            raise PolicyError(f"rules[{index}] must contain exactly the required rule fields")
        for key in SELECTOR_MAX_LENGTH:
            if not _selector_list(rule.get(key), key):
                raise PolicyError(f"rules[{index}].{key} must contain 1 to 128 unique bounded strings")
        if rule.get("effect") not in {"ALLOW", "DENY", "REVIEW_REQUIRED"}:
            raise PolicyError(f"rules[{index}].effect is unsupported")
        if not _text(rule["id"], "rule.id", max_length=128):
            raise PolicyError(f"rules[{index}].id is invalid")
    return policy


def load_request(path: str | Path) -> dict[str, Any]:
    request = _load(path, max_bytes=MAX_REQUEST_BYTES)
    if not set(request).issubset(REQUEST_KEYS):
        raise PolicyError("request contains unknown fields")
    required = REQUEST_KEYS - {"delegation_chain", "policy_version"}
    for key in required:
        if not _text(request.get(key), f"request.{key}"):
            raise PolicyError(f"request.{key} must be a non-empty string of at most 1024 characters")
    if "policy_version" in request and not _text(request["policy_version"], "policy_version"):
        raise PolicyError("request.policy_version must be a non-empty string")
    chain = request.get("delegation_chain", [])
    if (
        not isinstance(chain, list)
        or len(chain) > 32
        or not all(_text(item, "delegation_chain") for item in chain)
    ):
        raise PolicyError("delegation_chain must be an array of at most 32 non-empty strings")
    return request


def _time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not RFC3339.fullmatch(value) or value.endswith("-00:00"):
        raise PolicyError(f"{field} must be RFC3339 with an explicit timezone")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PolicyError(f"{field} is invalid") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise PolicyError(f"{field} must include a timezone")
    return result.astimezone(timezone.utc)


def evaluate(
    policy: dict[str, Any],
    request: dict[str, Any],
    *,
    now: datetime | None = None,
) -> Evaluation:
    version = policy.get("version", "UNKNOWN") if isinstance(policy, dict) else "UNKNOWN"
    if not isinstance(version, str):
        version = "UNKNOWN"

    def deny(code: str, message: str) -> Evaluation:
        return Evaluation(Decision.DENY, code, message, version)

    try:
        if not isinstance(policy, dict) or set(policy) != POLICY_KEYS:
            return deny("POLICY_INVALID", "Policy shape is invalid.")
        if policy.get("default_effect") != "DENY":
            return deny("POLICY_INVALID", "Policy is not deny-by-default.")
        rules = policy.get("rules")
        if not isinstance(rules, list) or len(rules) > MAX_RULES:
            return deny("POLICY_INVALID", "Policy rules are invalid.")
        if not _text(policy.get("version"), "version", max_length=POLICY_VERSION_MAX_LENGTH):
            return deny("POLICY_INVALID", "Policy version is invalid.")
        if not isinstance(request, dict) or not set(request).issubset(REQUEST_KEYS):
            return deny("REQUEST_INVALID", "Request shape is invalid.")
        required = REQUEST_KEYS - {"delegation_chain", "policy_version"}
        if any(not _text(request.get(key), key) for key in required):
            return deny("REQUEST_INVALID", "Required request fields are missing or invalid.")
        if "policy_version" in request:
            if not _text(request["policy_version"], "policy_version", max_length=POLICY_VERSION_MAX_LENGTH):
                return deny("REQUEST_INVALID", "Policy version reference is invalid.")
            if request["policy_version"] != policy["version"]:
                return deny("POLICY_VERSION_MISMATCH", "Request policy version does not match loaded policy.")
        try:
            issued = _time(request["issued_at"], "issued_at")
            expires = _time(request["expires_at"], "expires_at")
        except PolicyError:
            return deny("REQUEST_INVALID", "Request timestamp syntax is invalid.")
        if now is not None and (
            not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None
        ):
            return deny("CLOCK_INVALID", "Evaluation clock must be timezone-aware.")
        current = (now if now is not None else datetime.now(timezone.utc)).astimezone(timezone.utc)
        if expires <= issued:
            return deny("INVALID_VALIDITY_WINDOW", "Expiry must follow issue time.")
        if current < issued:
            return deny("NOT_YET_VALID", "Request is not yet valid.")
        if current >= expires:
            return deny("EXPIRED", "Request has expired.")
        chain = request.get("delegation_chain", [])
        if (
            not isinstance(chain, list)
            or len(chain) > 32
            or not all(_text(item, "delegation_chain") for item in chain)
        ):
            return deny("DELEGATION_INVALID", "Delegation chain malformed.")
        if len(chain) != len(set(chain)) or request["principal"] in chain:
            return deny("DELEGATION_CYCLE", "Delegation chain contains a cycle.")

        matches: list[str] = []
        for rule in rules:
            if not isinstance(rule, dict) or set(rule) != RULE_KEYS:
                return deny("POLICY_INVALID", "Policy rule shape is invalid.")
            if any(not _selector_list(rule.get(key), key) for key in SELECTOR_MAX_LENGTH):
                return deny("POLICY_INVALID", "Policy rule selectors are invalid.")
            if rule.get("effect") not in {"ALLOW", "DENY", "REVIEW_REQUIRED"}:
                return deny("POLICY_INVALID", "Policy contains an unknown effect.")
            if not _text(rule["id"], "rule.id", max_length=128):
                return deny("POLICY_INVALID", "Policy rule ID is invalid.")
            if (
                request["principal"] in rule["principals"]
                and request["action"] in rule["actions"]
                and request["target"] in rule["targets"]
                and request["scope"] in rule["scopes"]
            ):
                matches.append(rule["effect"])

        if "DENY" in matches:
            return deny("EXPLICIT_DENY", "At least one matching rule explicitly denies this request.")
        if "REVIEW_REQUIRED" in matches:
            return Evaluation(
                Decision.REVIEW_REQUIRED, "APPROVAL_REQUIRED",
                "A matching rule requires external approval.", version,
            )
        if "ALLOW" in matches:
            return Evaluation(
                Decision.ALLOW, "EXPLICIT_MATCH",
                "An explicit rule authorizes this exact request.", version,
            )
        return deny("NO_MATCH", "No explicit rule authorizes this exact request.")
    except (PolicyError, TypeError, ValueError, KeyError, AttributeError):
        return deny("EVALUATION_ERROR", "Invalid input; request denied.")


PROTOCOL_REQUEST_KEYS = {
    "protocol_version", "message_type", "request_id", "issued_at", "expires_at",
    "principal", "action", "target", "scope", "policy_version", "provenance_ref",
}
PROTOCOL_REQUEST_REQUIRED = PROTOCOL_REQUEST_KEYS - {"provenance_ref"}
UUID_V4 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _decode_json_object(raw: bytes, *, max_bytes: int, label: str) -> dict[str, Any]:
    if not isinstance(raw, bytes) or not raw or len(raw) > max_bytes:
        raise PolicyError(f"{label} JSON size is invalid")
    _check_json_depth(raw)
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise PolicyError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    _reject_surrogates(value)
    if not isinstance(value, dict):
        raise PolicyError(f"{label} JSON must be an object")
    return value


def evaluate_protocol(
    policy: dict[str, Any],
    envelope: dict[str, Any],
    *,
    now: datetime | None = None,
) -> Evaluation:
    """Evaluate a complete MASG v1.0.0 authorization request envelope.

    This entry point enforces the language-neutral envelope contract before
    delegating to the local policy evaluator. It does not authenticate principal
    identity or mediate the protected side effect.
    """
    version = policy.get("version", "UNKNOWN") if isinstance(policy, dict) else "UNKNOWN"

    def deny(code: str, message: str) -> Evaluation:
        return Evaluation(Decision.DENY, code, message, version if isinstance(version, str) else "UNKNOWN")

    if not isinstance(envelope, dict) or not PROTOCOL_REQUEST_REQUIRED.issubset(envelope):
        return deny("REQUEST_INVALID", "Protocol request is missing required fields.")
    if not set(envelope).issubset(PROTOCOL_REQUEST_KEYS):
        return deny("REQUEST_INVALID", "Protocol request contains unknown fields.")
    if envelope.get("protocol_version") != "1.0.0" or envelope.get("message_type") != "authorization_request":
        return deny("REQUEST_INVALID", "Protocol version or message type is unsupported.")
    if not isinstance(envelope.get("request_id"), str) or not UUID_V4.fullmatch(envelope["request_id"]):
        return deny("REQUEST_INVALID", "Request identifier must be a canonical lowercase UUIDv4.")
    field_limits = {"principal": 1024, "action": 256, "target": 512, "scope": 512, "policy_version": 128}
    for field, limit in field_limits.items():
        if not _text(envelope.get(field), field, max_length=limit):
            return deny("REQUEST_INVALID", f"Request field {field} is invalid.")
    if "provenance_ref" in envelope:
        provenance = envelope["provenance_ref"]
        if not isinstance(provenance, str) or len(provenance) > 2048:
            return deny("REQUEST_INVALID", "Provenance reference is invalid.")
    internal_request = {
        field: envelope[field]
        for field in ("principal", "action", "target", "scope", "request_id", "issued_at", "expires_at", "policy_version")
    }
    return evaluate(policy, internal_request, now=now)


def evaluate_protocol_json(
    policy_json: bytes,
    request_json: bytes,
    *,
    now: datetime | None = None,
) -> Evaluation:
    """Strictly parse and evaluate complete v1.0.0 JSON documents.

    Duplicate keys, invalid UTF-8, non-standard constants, excessive nesting,
    non-object top-level values, and oversized documents fail closed.
    """
    try:
        policy = _decode_json_object(policy_json, max_bytes=MAX_POLICY_BYTES, label="Policy")
    except PolicyError:
        return Evaluation(Decision.DENY, "POLICY_INVALID", "Policy JSON is invalid.", "UNKNOWN")
    version = policy.get("version", "UNKNOWN")
    if not isinstance(version, str):
        version = "UNKNOWN"
    try:
        envelope = _decode_json_object(request_json, max_bytes=MAX_REQUEST_BYTES, label="Request")
    except PolicyError:
        return Evaluation(Decision.DENY, "REQUEST_INVALID", "Request JSON is invalid.", version)
    return evaluate_protocol(policy, envelope, now=now)


def evaluate_files(
    policy_path: str | Path,
    request_path: str | Path,
    *,
    replay_db: str | Path | None = None,
) -> Evaluation:
    try:
        policy = load_policy(policy_path)
        request = load_request(request_path)
        result = evaluate(policy, request)
        if result.decision is not Decision.ALLOW or replay_db is None:
            return result
        try:
            accepted = ReplayStore(replay_db).consume(request)
        except ReplayStoreError:
            return Evaluation(
                Decision.DENY, "REPLAY_STORE_UNAVAILABLE",
                "Replay protection unavailable; request denied.", result.policy_version,
            )
        if not accepted:
            return Evaluation(
                Decision.DENY, "REPLAY_DETECTED",
                "Request ID has already been consumed; request denied.", result.policy_version,
            )
        return result
    except PolicyError as exc:
        return Evaluation(Decision.DENY, "INPUT_INVALID", str(exc), "UNKNOWN")
