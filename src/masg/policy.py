"""Deny-by-default local evaluator. Not an identity provider or sandbox."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from .models import Decision, Evaluation

class PolicyError(ValueError):
    pass

def _load(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyError(str(exc)) from exc
    if not isinstance(value, dict):
        raise PolicyError("top-level JSON must be an object")
    return value

def load_policy(path: str | Path) -> dict[str, Any]:
    policy = _load(path)
    if not isinstance(policy.get("version"), str) or not policy["version"]:
        raise PolicyError("policy.version must be a non-empty string")
    if policy.get("default_effect") != "DENY":
        raise PolicyError("default_effect must be DENY")
    if not isinstance(policy.get("rules"), list):
        raise PolicyError("policy.rules must be an array")
    for i, rule in enumerate(policy["rules"]):
        if not isinstance(rule, dict):
            raise PolicyError(f"rules[{i}] must be an object")
        for key in ("principals", "actions", "targets", "scopes"):
            values = rule.get(key)
            if not isinstance(values, list) or not values or not all(isinstance(x, str) and x for x in values):
                raise PolicyError(f"rules[{i}].{key} must be a non-empty string array")
        if rule.get("effect") not in {"ALLOW", "DENY", "REVIEW_REQUIRED"}:
            raise PolicyError(f"rules[{i}].effect is unsupported")
    return policy

def load_request(path: str | Path) -> dict[str, Any]:
    request = _load(path)
    for key in ("principal", "action", "target", "scope", "request_id", "issued_at", "expires_at"):
        if not isinstance(request.get(key), str) or not request[key]:
            raise PolicyError(f"request.{key} must be a non-empty string")
    chain = request.get("delegation_chain", [])
    if not isinstance(chain, list) or not all(isinstance(x, str) and x for x in chain):
        raise PolicyError("delegation_chain must be a string array")
    return request

def _time(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise PolicyError(f"{field} must be ISO-8601")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PolicyError(f"{field} is invalid") from exc
    if result.tzinfo is None:
        raise PolicyError(f"{field} must include timezone")
    return result.astimezone(timezone.utc)

def evaluate(policy: dict[str, Any], request: dict[str, Any], *, now: datetime | None = None) -> Evaluation:
    version = str(policy.get("version", "UNKNOWN"))
    def deny(code: str, message: str) -> Evaluation:
        return Evaluation(Decision.DENY, code, message, version)
    try:
        if policy.get("default_effect") != "DENY" or not isinstance(policy.get("rules"), list):
            return deny("POLICY_INVALID", "Policy invalid or not deny-by-default.")
        keys = ("principal", "action", "target", "scope", "request_id", "issued_at", "expires_at")
        if any(not isinstance(request.get(k), str) or not request[k] for k in keys):
            return deny("REQUEST_INVALID", "Required request fields missing or invalid.")
        issued, expires = _time(request["issued_at"], "issued_at"), _time(request["expires_at"], "expires_at")
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if expires <= issued:
            return deny("INVALID_VALIDITY_WINDOW", "Expiry must follow issue time.")
        if current < issued:
            return deny("NOT_YET_VALID", "Request is not yet valid.")
        if current >= expires:
            return deny("EXPIRED", "Request has expired.")
        chain = request.get("delegation_chain", [])
        if not isinstance(chain, list) or any(not isinstance(x, str) or not x for x in chain):
            return deny("DELEGATION_INVALID", "Delegation chain malformed.")
        if len(chain) != len(set(chain)) or request["principal"] in chain:
            return deny("DELEGATION_CYCLE", "Delegation chain contains a cycle.")
        for rule in policy["rules"]:
            if not isinstance(rule, dict) or any(not isinstance(rule.get(k), list) for k in ("principals","actions","targets","scopes")):
                return deny("POLICY_INVALID", "Policy rule malformed.")
            if (request["principal"] in rule["principals"] and request["action"] in rule["actions"]
                and request["target"] in rule["targets"] and request["scope"] in rule["scopes"]):
                effect = rule.get("effect")
                if effect == "ALLOW":
                    return Evaluation(Decision.ALLOW,"EXPLICIT_MATCH","Exact explicit rule matched.",version)
                if effect == "REVIEW_REQUIRED":
                    return Evaluation(Decision.REVIEW_REQUIRED,"APPROVAL_REQUIRED","External approval required.",version)
                if effect == "DENY":
                    return deny("EXPLICIT_DENY","Explicit rule denies request.")
                return deny("POLICY_INVALID","Matched rule has unknown effect.")
        return deny("NO_MATCH","No explicit rule authorizes this exact request.")
    except (PolicyError, TypeError, ValueError, KeyError):
        return deny("EVALUATION_ERROR","Invalid input; request denied.")

def evaluate_files(policy_path: str | Path, request_path: str | Path) -> Evaluation:
    try:
        return evaluate(load_policy(policy_path), load_request(request_path))
    except PolicyError as exc:
        return Evaluation(Decision.DENY,"INPUT_INVALID",str(exc),"UNKNOWN")
