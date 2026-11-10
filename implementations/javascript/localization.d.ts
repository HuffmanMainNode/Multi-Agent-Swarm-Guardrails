export type TranslationStatus =
  | "SOURCE"
  | "UNTRANSLATED"
  | "MACHINE_DRAFT"
  | "HUMAN_REVIEWED"
  | "NEEDS_REVISION";

export interface TranslationMessage {
  text: string;
  status: TranslationStatus;
  review?: {
    reviewer: string;
    reviewed_at: string;
    notes?: string;
  };
}

export interface TranslationPack {
  schema_version: "1.0.0";
  locale: string;
  source_locale: string;
  catalog_version: string;
  text_direction?: "ltr" | "rtl" | "auto";
  messages: Record<string, TranslationMessage>;
}

export interface ResolvedMessage {
  text: string;
  locale: string;
  status: "SOURCE" | "MACHINE_DRAFT" | "HUMAN_REVIEWED";
  usedFallback: boolean;
}

export declare function resolveMessage(
  sourcePack: TranslationPack,
  localePack: TranslationPack | null | undefined,
  messageId: string,
  options?: { allowMachineDrafts?: boolean },
): ResolvedMessage;

export declare function createTranslationTemplate(
  sourcePack: TranslationPack,
  locale: string,
  textDirection?: "ltr" | "rtl" | "auto",
): TranslationPack;
