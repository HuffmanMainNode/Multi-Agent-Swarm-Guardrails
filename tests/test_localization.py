"""Tests for the portable, offline MASG localization resolver."""
import copy
import json
from pathlib import Path
import unittest

from masg.localization import LocalizationError, create_translation_template, resolve_message

ROOT = Path(__file__).resolve().parents[1]


def load_pack(path):
    return json.loads(path.read_text(encoding="utf-8"))


class LocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load_pack(ROOT / "localization/locales/en/messages.json")
        cls.template = load_pack(ROOT / "localization/locales/es/messages.template.json")
        cls.message_id = "masg.ui.authorization_denied"

    def test_untranslated_template_falls_back_to_source(self):
        result = resolve_message(self.source, self.template, self.message_id)
        self.assertEqual(result.text, "Authorization denied")
        self.assertEqual(result.locale, "en")
        self.assertTrue(result.used_fallback)

    def test_human_reviewed_translation_is_used(self):
        locale = copy.deepcopy(self.template)
        locale["messages"][self.message_id] = {
            "text": "Autorización denegada",
            "status": "HUMAN_REVIEWED",
            "review": {"reviewer": "reviewer-1", "reviewed_at": "2026-11-10T05:00:00Z"},
        }
        result = resolve_message(self.source, locale, self.message_id)
        self.assertEqual(result.text, "Autorización denegada")
        self.assertEqual(result.locale, "es")
        self.assertFalse(result.used_fallback)

    def test_machine_draft_requires_explicit_opt_in(self):
        locale = copy.deepcopy(self.template)
        locale["messages"][self.message_id] = {"text": "Borrador automático", "status": "MACHINE_DRAFT"}
        default = resolve_message(self.source, locale, self.message_id)
        opted_in = resolve_message(self.source, locale, self.message_id, allow_machine_drafts=True)
        self.assertTrue(default.used_fallback)
        self.assertEqual(opted_in.text, "Borrador automático")

    def test_needs_revision_always_falls_back(self):
        locale = copy.deepcopy(self.template)
        locale["messages"][self.message_id] = {"text": "Texto cuestionado", "status": "NEEDS_REVISION"}
        result = resolve_message(self.source, locale, self.message_id, allow_machine_drafts=True)
        self.assertTrue(result.used_fallback)
        self.assertEqual(result.text, "Authorization denied")

    def test_human_reviewed_translation_requires_review_metadata(self):
        locale = copy.deepcopy(self.template)
        locale["messages"][self.message_id] = {"text": "Autorización denegada", "status": "HUMAN_REVIEWED"}
        with self.assertRaises(LocalizationError):
            resolve_message(self.source, locale, self.message_id)

    def test_catalog_version_mismatch_is_rejected(self):
        locale = copy.deepcopy(self.template)
        locale["catalog_version"] = "2.0.0"
        with self.assertRaises(LocalizationError):
            resolve_message(self.source, locale, self.message_id)

    def test_unknown_message_id_is_not_silently_translated(self):
        with self.assertRaises(KeyError):
            resolve_message(self.source, self.template, "masg.ui.not_a_real_message")

    def test_template_generator_creates_all_untranslated_ids(self):
        generated = create_translation_template(self.source, "fr-CA", text_direction="ltr")
        self.assertEqual(generated["locale"], "fr-CA")
        self.assertEqual(generated["source_locale"], "en")
        self.assertEqual(set(generated["messages"]), set(self.source["messages"]))
        self.assertTrue(all(
            item == {"text": "", "status": "UNTRANSLATED"}
            for item in generated["messages"].values()
        ))

    def test_template_generator_rejects_source_locale_and_bad_direction(self):
        with self.assertRaises(LocalizationError):
            create_translation_template(self.source, "en")
        with self.assertRaises(LocalizationError):
            create_translation_template(self.source, "fr", text_direction="diagonal")

    def test_missing_locale_entry_falls_back(self):
        locale = copy.deepcopy(self.template)
        locale["messages"].pop(self.message_id)
        result = resolve_message(self.source, locale, self.message_id)
        self.assertTrue(result.used_fallback)
        self.assertEqual(result.text, "Authorization denied")


if __name__ == "__main__":
    unittest.main()
