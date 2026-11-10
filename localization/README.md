# MASG Localization

This directory contains portable, offline-capable human-language terminology and message packs.

## Current status

- English is the authoritative source locale.
- The English message catalog and core concept glossary are the source materials.
- The Spanish file is an untranslated template. It is not a Spanish translation and must not be presented as localized content.
- No non-English pack is currently marked HUMAN_REVIEWED.
- No translation service, API, telemetry, or network dependency is required.

## Package format

Translation packs use `schemas/translation-pack.schema.json` and BCP 47 locale tags. Message IDs are stable keys. A pack records the source locale, catalog version, text, translation status, and optional review metadata.

Statuses:
- `SOURCE`: authoritative source text, used only in the source locale.
- `UNTRANSLATED`: empty placeholder awaiting a contributor.
- `MACHINE_DRAFT`: generated or machine-assisted text not approved for reliance.
- `HUMAN_REVIEWED`: reviewed by a named human contributor and timestamped.
- `NEEDS_REVISION`: a reviewer found an issue; consumers should fall back to source text.

Consumers must fall back to the English source for missing, invalid, or unreviewed strings unless the user explicitly opts into draft translations. Security-critical terms should not be used from unreviewed translations in operational decisions.

## Review policy

1. Preserve the stable message ID and source meaning.
2. Record locale using a valid BCP 47 tag.
3. Never translate JSON keys, protocol fields, enum values, reason codes, concept IDs, cryptographic material, or machine identifiers.
4. Mark machine-generated content MACHINE_DRAFT, never HUMAN_REVIEWED.
5. A HUMAN_REVIEWED entry requires a reviewer identifier and review timestamp.
6. Prefer a second independent reviewer for security-critical terminology.
7. Record unresolved ambiguity and regional variants rather than forcing false equivalence.
8. When source text changes, re-review translations affected by that change.
9. Do not remove the source text or silently alter its meaning.
10. Translation review is not a security certification or guarantee of universal correctness.

## Contributing a language

Copy `locales/es/messages.template.json`, change the locale to your BCP 47 tag, and submit a pull request. Leave untranslated values empty. Add human translations only when you can review them competently. Include regional context where relevant.

The project welcomes new language packs and corrections. Contributors should disclose machine assistance and avoid claiming native-speaker review they did not perform.
