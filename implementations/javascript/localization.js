// Offline localization resolver for MASG translation packs.
// Human-reviewed text is used by default; machine drafts require explicit opt-in.

const LOCALE = /^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$/;
const VERSION = /^[0-9]+\.[0-9]+\.[0-9]+$/;
const MESSAGE_ID = /^[a-z][a-z0-9]*(?:\.[a-z0-9_-]+)+$/;
const STATUSES = new Set(["SOURCE", "UNTRANSLATED", "MACHINE_DRAFT", "HUMAN_REVIEWED", "NEEDS_REVISION"]);

function record(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function fail(message) {
  throw new TypeError(message);
}

function validateSourcePack(pack) {
  if (!record(pack) || pack.schema_version !== "1.0.0") fail("invalid source pack");
  if (typeof pack.locale !== "string" || !LOCALE.test(pack.locale)) fail("invalid source locale syntax");
  if (pack.source_locale !== pack.locale) fail("source pack locale must equal source_locale");
  if (typeof pack.catalog_version !== "string" || !VERSION.test(pack.catalog_version)) fail("invalid catalog version");
  if (!record(pack.messages) || Object.keys(pack.messages).length === 0) fail("source messages must be a non-empty object");
  for (const [id, item] of Object.entries(pack.messages)) {
    if (!MESSAGE_ID.test(id) || !record(item) || item.status !== "SOURCE" ||
        typeof item.text !== "string" || item.text.length === 0) {
      fail(`invalid source message: ${id}`);
    }
  }
}

function validateLocalePack(pack, sourcePack) {
  if (!record(pack) || pack.schema_version !== "1.0.0") fail("invalid locale pack");
  if (typeof pack.locale !== "string" || !LOCALE.test(pack.locale)) fail("invalid locale syntax");
  if (pack.locale.toLowerCase() === sourcePack.locale.toLowerCase()) fail("use the source pack for the source locale");
  if (typeof pack.source_locale !== "string" ||
      pack.source_locale.toLowerCase() !== sourcePack.locale.toLowerCase()) {
    fail("locale pack source_locale does not match source pack");
  }
  if (pack.catalog_version !== sourcePack.catalog_version) fail("locale pack catalog version does not match source pack");
  if (!record(pack.messages)) fail("locale messages must be an object");
  for (const [id, item] of Object.entries(pack.messages)) {
    if (!MESSAGE_ID.test(id) || !Object.hasOwn(sourcePack.messages, id) || !record(item)) {
      fail(`unknown or invalid locale message: ${id}`);
    }
    const { status, text } = item;
    if (typeof status !== "string" || !STATUSES.has(status) || status === "SOURCE" || typeof text !== "string") {
      fail(`invalid translation status or text: ${id}`);
    }
    if (status === "UNTRANSLATED" && text.length !== 0) fail(`untranslated message must be empty: ${id}`);
    if (status !== "UNTRANSLATED" && text.length === 0) fail(`translation text is empty: ${id}`);
    if (status === "HUMAN_REVIEWED") {
      if (!record(item.review) || typeof item.review.reviewer !== "string" ||
          item.review.reviewer.trim().length === 0 ||
          typeof item.review.reviewed_at !== "string" || item.review.reviewed_at.trim().length === 0) {
        fail(`human-reviewed message requires reviewer metadata: ${id}`);
      }
    }
  }
}

/**
 * Resolve one stable message ID.
 * UNTRANSLATED and NEEDS_REVISION always fall back to source.
 * MACHINE_DRAFT is used only when allowMachineDrafts is true.
 */
export function resolveMessage(sourcePack, localePack, messageId, options = {}) {
  validateSourcePack(sourcePack);
  if (typeof messageId !== "string" || !MESSAGE_ID.test(messageId)) fail("invalid message identifier");
  if (!Object.hasOwn(sourcePack.messages, messageId)) throw new RangeError(`unknown message identifier: ${messageId}`);

  const source = sourcePack.messages[messageId];
  const fallback = () => ({
    text: source.text,
    locale: sourcePack.locale,
    status: "SOURCE",
    usedFallback: true,
  });
  if (localePack === null || localePack === undefined) return fallback();
  validateLocalePack(localePack, sourcePack);
  const translated = localePack.messages[messageId];
  if (!translated) return fallback();
  if (translated.status === "HUMAN_REVIEWED" ||
      (translated.status === "MACHINE_DRAFT" && options.allowMachineDrafts === true)) {
    return {
      text: translated.text,
      locale: localePack.locale,
      status: translated.status,
      usedFallback: false,
    };
  }
  return fallback();
}
