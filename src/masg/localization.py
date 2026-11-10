"""Small, offline localization resolver for validated MASG message packs.

The resolver intentionally uses reviewed translations by default. It does not
perform machine translation, network access, or protocol-field translation.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import re
from typing import Any

_LOCALE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_MESSAGE_ID = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9_-]+)+$")
_STATUSES = {"SOURCE", "UNTRANSLATED", "MACHINE_DRAFT", "HUMAN_REVIEWED", "NEEDS_REVISION"}


class LocalizationError(ValueError):
    """Raised when a localization pack is structurally unsafe or inconsistent."""


@dataclass(frozen=True)
class ResolvedMessage:
    text: str
    locale: str
    status: str
    used_fallback: bool


def _record(value: Any) -> bool:
    return isinstance(value, Mapping)


def _validate_message_id(message_id: Any) -> bool:
    return isinstance(message_id, str) and _MESSAGE_ID.fullmatch(message_id) is not None


def _validate_source_pack(pack: Mapping[str, Any]) -> None:
    if pack.get("schema_version") != "1.0.0":
        raise LocalizationError("unsupported source pack schema version")
    locale = pack.get("locale")
    if not isinstance(locale, str) or not _LOCALE.fullmatch(locale):
        raise LocalizationError("invalid source locale syntax")
    if pack.get("source_locale") != locale:
        raise LocalizationError("source pack locale must equal source_locale")
    if not isinstance(pack.get("catalog_version"), str) or not _VERSION.fullmatch(pack["catalog_version"]):
        raise LocalizationError("invalid catalog version")
    messages = pack.get("messages")
    if not _record(messages) or not messages:
        raise LocalizationError("source messages must be a non-empty object")
    for message_id, item in messages.items():
        if not _validate_message_id(message_id) or not _record(item):
            raise LocalizationError("invalid source message entry")
        if item.get("status") != "SOURCE" or not isinstance(item.get("text"), str) or not item["text"]:
            raise LocalizationError(f"source message {message_id!r} must have non-empty SOURCE text")


def _validate_locale_pack(pack: Mapping[str, Any], source_pack: Mapping[str, Any]) -> None:
    if pack.get("schema_version") != "1.0.0":
        raise LocalizationError("unsupported locale pack schema version")
    locale = pack.get("locale")
    if not isinstance(locale, str) or not _LOCALE.fullmatch(locale):
        raise LocalizationError("invalid locale syntax")
    if locale.casefold() == str(source_pack["locale"]).casefold():
        raise LocalizationError("use the source pack for the source locale")
    source_locale = pack.get("source_locale")
    if not isinstance(source_locale, str) or source_locale.casefold() != source_pack["locale"].casefold():
        raise LocalizationError("locale pack source_locale does not match source pack")
    if pack.get("catalog_version") != source_pack["catalog_version"]:
        raise LocalizationError("locale pack catalog version does not match source pack")
    messages = pack.get("messages")
    if not _record(messages):
        raise LocalizationError("locale messages must be an object")
    source_ids = source_pack["messages"]
    for message_id, item in messages.items():
        if not _validate_message_id(message_id) or message_id not in source_ids or not _record(item):
            raise LocalizationError(f"unknown or invalid locale message {message_id!r}")
        status = item.get("status")
        text = item.get("text")
        if not isinstance(status, str) or status not in _STATUSES - {"SOURCE"} or not isinstance(text, str):
            raise LocalizationError(f"invalid translation status or text for {message_id!r}")
        if status == "UNTRANSLATED" and text:
            raise LocalizationError(f"untranslated message {message_id!r} must have empty text")
        if status != "UNTRANSLATED" and not text:
            raise LocalizationError(f"translation {message_id!r} must have non-empty text")
        if status == "HUMAN_REVIEWED":
            review = item.get("review")
            if not _record(review) or not isinstance(review.get("reviewer"), str) or not review["reviewer"].strip():
                raise LocalizationError(f"human-reviewed message {message_id!r} requires reviewer metadata")
            if not isinstance(review.get("reviewed_at"), str) or not review["reviewed_at"].strip():
                raise LocalizationError(f"human-reviewed message {message_id!r} requires reviewed_at metadata")


def resolve_message(
    source_pack: Mapping[str, Any],
    locale_pack: Mapping[str, Any] | None,
    message_id: str,
    *,
    allow_machine_drafts: bool = False,
) -> ResolvedMessage:
    """Resolve a message, falling back to source unless review policy permits it.

    MACHINE_DRAFT is used only when allow_machine_drafts=True. UNTRANSLATED and
    NEEDS_REVISION always fall back. Missing locale entries also fall back.
    """
    if not _record(source_pack):
        raise LocalizationError("source pack must be an object")
    if not _validate_message_id(message_id):
        raise LocalizationError("invalid message identifier")
    _validate_source_pack(source_pack)
    source_item = source_pack["messages"].get(message_id)
    if source_item is None:
        raise KeyError(message_id)

    if locale_pack is None:
        return ResolvedMessage(source_item["text"], source_pack["locale"], "SOURCE", True)
    if not _record(locale_pack):
        raise LocalizationError("locale pack must be an object")
    _validate_locale_pack(locale_pack, source_pack)
    translated = locale_pack["messages"].get(message_id)
    if translated is None:
        return ResolvedMessage(source_item["text"], source_pack["locale"], "SOURCE", True)

    status = translated["status"]
    if status == "HUMAN_REVIEWED" or (status == "MACHINE_DRAFT" and allow_machine_drafts is True):
        return ResolvedMessage(translated["text"], locale_pack["locale"], status, False)
    return ResolvedMessage(source_item["text"], source_pack["locale"], "SOURCE", True)

def create_translation_template(
    source_pack: Mapping[str, Any],
    locale: str,
    *,
    text_direction: str = "auto",
) -> dict[str, Any]:
    """Create an untranslated pack skeleton for any syntactically valid locale tag."""
    if not _record(source_pack):
        raise LocalizationError("source pack must be an object")
    _validate_source_pack(source_pack)
    if not isinstance(locale, str) or not _LOCALE.fullmatch(locale):
        raise LocalizationError("invalid locale syntax")
    if locale.casefold() == source_pack["locale"].casefold():
        raise LocalizationError("target locale must differ from source locale")
    if not isinstance(text_direction, str) or text_direction not in {"ltr", "rtl", "auto"}:
        raise LocalizationError("text_direction must be ltr, rtl, or auto")
    return {
        "schema_version": "1.0.0",
        "locale": locale,
        "source_locale": source_pack["locale"],
        "catalog_version": source_pack["catalog_version"],
        "text_direction": text_direction,
        "messages": {
            message_id: {"text": "", "status": "UNTRANSLATED"}
            for message_id in source_pack["messages"]
        },
    }
