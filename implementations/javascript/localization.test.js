import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { resolveMessage } from "./localization.js";

const source = JSON.parse(await readFile(new URL("../../localization/locales/en/messages.json", import.meta.url), "utf8"));
const template = JSON.parse(await readFile(new URL("../../localization/locales/es/messages.template.json", import.meta.url), "utf8"));
const messageId = "masg.ui.authorization_denied";

test("untranslated template falls back to authoritative source", () => {
  const result = resolveMessage(source, template, messageId);
  assert.equal(result.text, "Authorization denied");
  assert.equal(result.locale, "en");
  assert.equal(result.usedFallback, true);
});

test("human-reviewed translation is selected", () => {
  const locale = structuredClone(template);
  locale.messages[messageId] = {
    text: "Autorización denegada",
    status: "HUMAN_REVIEWED",
    review: {reviewer: "reviewer-1", reviewed_at: "2026-11-10T05:00:00Z"},
  };
  const result = resolveMessage(source, locale, messageId);
  assert.equal(result.text, "Autorización denegada");
  assert.equal(result.locale, "es");
  assert.equal(result.usedFallback, false);
});

test("machine draft requires explicit opt-in", () => {
  const locale = structuredClone(template);
  locale.messages[messageId] = {text: "Borrador automático", status: "MACHINE_DRAFT"};
  assert.equal(resolveMessage(source, locale, messageId).usedFallback, true);
  assert.equal(resolveMessage(source, locale, messageId, {allowMachineDrafts: true}).text, "Borrador automático");
});

test("needs-revision text always falls back", () => {
  const locale = structuredClone(template);
  locale.messages[messageId] = {text: "Texto cuestionado", status: "NEEDS_REVISION"};
  assert.equal(resolveMessage(source, locale, messageId, {allowMachineDrafts: true}).text, "Authorization denied");
});

test("human-reviewed entry requires reviewer and timestamp", () => {
  const locale = structuredClone(template);
  locale.messages[messageId] = {text: "Autorización denegada", status: "HUMAN_REVIEWED"};
  assert.throws(() => resolveMessage(source, locale, messageId), /reviewer metadata/);
});

test("catalog mismatch and unknown message IDs are rejected", () => {
  const locale = structuredClone(template);
  locale.catalog_version = "2.0.0";
  assert.throws(() => resolveMessage(source, locale, messageId), /catalog version/);
  assert.throws(() => resolveMessage(source, template, "masg.ui.not_real"), /unknown message identifier/);
});

test("missing locale entries fall back", () => {
  const locale = structuredClone(template);
  delete locale.messages[messageId];
  assert.equal(resolveMessage(source, locale, messageId).text, "Authorization denied");
});

test("malformed locale source type is rejected", () => {
  const locale = structuredClone(template);
  locale.source_locale = 42;
  assert.throws(() => resolveMessage(source, locale, messageId), /source_locale/);
});
