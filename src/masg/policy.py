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
MAX_RULES = 10_000
MAX_TEXT_LENGTH = 1_024
POLICY_KEYS = {"version", "default_effect", "rules"}
RULE_KEYS = {"id", "principals", "actions", "targets", "scopes", "effect"}
REQUEST_KEYS = {
    "principal", "action", "target", "scope", "request_id",
    "issued_at", "expires_at", "delegation_chain",
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


def _load(path: str | Path, *, max_bytes: int) -> dict[str, Any]:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise PolicyError(f"cannot read input: {exc}") from exc
    if len(raw) > max_bytes:
        raise PolicyError(f"input exceeds {max_bytes} byte limit")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PolicyError(f"invalid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise PolicyError("top-level JSON must be an object")
    return value


def _text(value: Any, field: str) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= MAX_TEXT_LENGTH


def load_policy(path: str | Path) -> dict[str, Any]:
    policy = _load(path, max_bytes=MAX_POLICY_BYTES)
    if set(policy) != POLICY_KEYS:
        raise PolicyError("policy must contain exactly version, default_effect, and rules")
    if not _text(policy.get("version"), "version"):
        raise PolicyError("policy.version must be a non-empty string of at most 1024 characters")
    if policy.get("default_effect") != "DENY":
        raise PolicyError("default_effect must be DENY")
    rules = policy.get("rules")
    if not isinstance(rules, list) or len(rules) > MAX_RULES:
        raise PolicyError(f"policy.rules must be an array of at most {MAX_RULES} rules")
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict) or not set(rule).issubset(RULE_KEYS):
            raise PolicyError(f"rules[{index}] has invalid shape or unknown fields")
        for key in ("principals", "actions", "targets", "scopes"):
            values = rule.get(key)
            if (
                not isinstance(values, list)
                or not values
                or len(values) > 1_024
                or not all(_text(item, f"rules[{index}].{key}") for item in values)
                or len(values) != len(set(values))
            ):
                raise PolicyError(f"rules[{index}].{key} must be a unique non-empty string array")
        if rule.get("effect") not in {"ALLOW", "DENY", "REVIEW_REQUIRED"}:
            raise PolicyError(f"rules[{index}].effect is unsupported")
        if "id" in rule and not _text(rule["id"], f"rules[{index}].id"):
            raise PolicyError(f"rules[{index}].id is invalid")
    return policy


def load_request(path: str | Path) -> dict[str, Any]:
    request = _load(path, max_bytes=MAX_REQUEST_BYTES)
    if not set(request).issubset(REQUEST_KEYS):
        raise PolicyError("request contains unknown fields")
    required = REQUEST_KEYS - {"delegation_chain"}
    for key in required:
        if not _text(request.get(key), f"request.{key}"):
            raise PolicyError(f"request.{key} must be a non-empty string of at most 1024 characters")
    chain = request.get("delegation_chain", [])
    if (
        not isinstance(chain, list)
        or len(chain) > 32
        or not all(_text(item, "delegation_chain") for item in chain)
    ):
        raise PolicyError("delegation_chain must be an array of at most 32 non-empty strings")
    return request


def _time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not RFC3339.fullmatch(value):
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
        if not _text(policy.get("version"), "version"):
            return deny("POLICY_INVALID", "Policy version is invalid.")
        if not isinstance(request, dict) or not set(request).issubset(REQUEST_KEYS):
            return deny("REQUEST_INVALID", "Request shape is invalid.")
        required = REQUEST_KEYS - {"delegation_chain"}
        if any(not _text(request.get(key), key) for key in required):
            return deny("REQUEST_INVALID", "Required request fields are missing or invalid.")
        issued = _time(request["issued_at"], "issued_at")
        expires = _time(request["expires_at"], "expires_at")
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
            if not isinstance(rule, dict) or not set(rule).issubset(RULE_KEYS):
                return deny("POLICY_INVALID", "Policy rule shape is invalid.")
            if any(
                not isinstance(rule.get(key), list)
                or not rule[key]
                or len(rule[key]) > 1_024
                or not all(_text(item, key) for item in rule[key])
                or len(rule[key]) != len(set(rule[key]))
                for key in ("principals", "actions", "targets", "scopes")
            ):
                return deny("POLICY_INVALID", "Policy rule selectors are invalid.")
            if rule.get("effect") not in {"ALLOW", "DENY", "REVIEW_REQUIRED"}:
                return deny("POLICY_INVALID", "Policy contains an unknown effect.")
            if "id" in rule and not _text(rule["id"], "rule.id"):
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
