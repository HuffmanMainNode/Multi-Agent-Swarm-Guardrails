// MASG v1.0.0 JavaScript reference evaluator.
// Policy decisions only: this module does not authenticate identities or mediate side effects.

export const PROTOCOL_VERSION = "1.0.0";
const MAX_POLICY_BYTES = 1_048_576;
const MAX_REQUEST_BYTES = 65_536;
const MAX_JSON_DEPTH = 32;
const MAX_RULES = 1_000;
const MAX_SELECTORS = 128;
const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const RFC3339 = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?(Z|[+-](?:0\d|1\d|2[0-3]):[0-5]\d)$/;

function deny(reasonCode, policyVersion = "UNKNOWN") {
  return { decision: "DENY", reason_code: reasonCode, policy_version: policyVersion };
}

function codePointLength(value) {
  return [...value].length;
}

function validText(value, max) {
  return typeof value === "string" &&
    value.trim().length > 0 &&
    codePointLength(value) <= max &&
    !hasUnpairedSurrogate(value);
}

function hasUnpairedSurrogate(value) {
  for (let i = 0; i < value.length; i += 1) {
    const code = value.charCodeAt(i);
    if (code >= 0xd800 && code <= 0xdbff) {
      const next = value.charCodeAt(i + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) return true;
      i += 1;
    } else if (code >= 0xdc00 && code <= 0xdfff) {
      return true;
    }
  }
  return false;
}

function parseStrictJSON(input, maxBytes) {
  let bytes;
  if (typeof input === "string") {
    bytes = Buffer.from(input, "utf8");
  } else if (input instanceof Uint8Array || Buffer.isBuffer(input)) {
    bytes = Buffer.from(input);
  } else {
    throw new Error("JSON input must be a UTF-8 string or byte array");
  }
  if (bytes.length === 0 || bytes.length > maxBytes) throw new Error("JSON size invalid");
  const source = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  let position = 0;

  function whitespace() {
    while (position < source.length && /[ \t\n\r]/.test(source[position])) position += 1;
  }

  function parseString() {
    const start = position;
    if (source[position] !== '"') throw new Error("expected JSON string");
    position += 1;
    while (position < source.length) {
      const char = source[position];
      if (char === '"') {
        position += 1;
        const value = JSON.parse(source.slice(start, position));
        if (hasUnpairedSurrogate(value)) throw new Error("unpaired Unicode surrogate");
        return value;
      }
      if (char === "\\") {
        position += 1;
        if (position >= source.length) throw new Error("incomplete string escape");
        position += 1;
      } else {
        if (source.charCodeAt(position) < 0x20) throw new Error("unescaped control character");
        position += 1;
      }
    }
    throw new Error("unterminated JSON string");
  }

  function parseValue(depth) {
    whitespace();
    if (position >= source.length) throw new Error("missing JSON value");
    const char = source[position];
    if (char === "{" || char === "[") {
      const nextDepth = depth + 1;
      if (nextDepth > MAX_JSON_DEPTH) throw new Error("JSON nesting too deep");
      if (char === "{") {
        position += 1;
        whitespace();
        const object = Object.create(null);
        const seen = new Set();
        if (source[position] === "}") {
          position += 1;
          return object;
        }
        while (true) {
          whitespace();
          const key = parseString();
          if (seen.has(key)) throw new Error("duplicate JSON object key");
          seen.add(key);
          whitespace();
          if (source[position] !== ":") throw new Error("missing object colon");
          position += 1;
          object[key] = parseValue(nextDepth);
          whitespace();
          if (source[position] === "}") {
            position += 1;
            return object;
          }
          if (source[position] !== ",") throw new Error("invalid object separator");
          position += 1;
        }
      }
      position += 1;
      whitespace();
      const array = [];
      if (source[position] === "]") {
        position += 1;
        return array;
      }
      while (true) {
        array.push(parseValue(nextDepth));
        whitespace();
        if (source[position] === "]") {
          position += 1;
          return array;
        }
        if (source[position] !== ",") throw new Error("invalid array separator");
        position += 1;
      }
    }
    if (char === '"') return parseString();
    if (source.startsWith("true", position)) {
      position += 4;
      return true;
    }
    if (source.startsWith("false", position)) {
      position += 5;
      return false;
    }
    if (source.startsWith("null", position)) {
      position += 4;
      return null;
    }
    const number = /^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/.exec(source.slice(position));
    if (number) {
      position += number[0].length;
      const parsed = JSON.parse(number[0]);
      if (!Number.isFinite(parsed)) throw new Error("non-finite number");
      return parsed;
    }
    throw new Error("invalid JSON value");
  }

  const result = parseValue(0);
  whitespace();
  if (position !== source.length) throw new Error("trailing JSON data");
  if (result === null || Array.isArray(result) || typeof result !== "object") {
    throw new Error("top-level JSON document must be an object");
  }
  return result;
}

function exactKeys(object, required, optional = []) {
  const keys = Object.keys(object);
  return required.every((key) => Object.hasOwn(object, key)) &&
    keys.every((key) => required.includes(key) || optional.includes(key));
}

function validSelectors(values, maxLength) {
  if (!Array.isArray(values) || values.length < 1 || values.length > MAX_SELECTORS) return false;
  const seen = new Set();
  for (const value of values) {
    if (!validText(value, maxLength) || seen.has(value)) return false;
    seen.add(value);
  }
  return true;
}

function validatePolicy(policy) {
  if (!exactKeys(policy, ["version", "default_effect", "rules"])) return false;
  if (!validText(policy.version, 128) || policy.default_effect !== "DENY") return false;
  if (!Array.isArray(policy.rules) || policy.rules.length > MAX_RULES) return false;
  for (const rule of policy.rules) {
    if (rule === null || typeof rule !== "object" || Array.isArray(rule)) return false;
    if (!exactKeys(rule, ["id", "principals", "actions", "targets", "scopes", "effect"])) return false;
    if (!validText(rule.id, 128) ||
        !validSelectors(rule.principals, 1024) ||
        !validSelectors(rule.actions, 256) ||
        !validSelectors(rule.targets, 512) ||
        !validSelectors(rule.scopes, 512) ||
        !["ALLOW", "DENY", "REVIEW_REQUIRED"].includes(rule.effect)) return false;
  }
  return true;
}

function timestampMicros(value) {
  if (typeof value !== "string") return null;
  const match = RFC3339.exec(value);
  if (!match || value.startsWith("0000-") || match[3] === "-00:00") return null;

  // Date.parse() may normalize impossible dates (for example, February 30)
  // instead of rejecting them. Validate RFC 3339 calendar/time components
  // explicitly so this evaluator agrees with strict parsers in other runtimes.
  const [year, month, day, hour, minute, second] = [
    Number(value.slice(0, 4)),
    Number(value.slice(5, 7)),
    Number(value.slice(8, 10)),
    Number(value.slice(11, 13)),
    Number(value.slice(14, 16)),
    Number(value.slice(17, 19)),
  ];
  if (month < 1 || month > 12 || hour > 23 || minute > 59 || second > 59) return null;
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const monthDays = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (day < 1 || day > monthDays[month - 1]) return null;

  const milliseconds = Date.parse(match[1] + match[3]);
  if (!Number.isFinite(milliseconds)) return null;
  const fraction = BigInt((match[2] || "").padEnd(6, "0") || "0");
  return BigInt(milliseconds) * 1000n + fraction;
}

function validateRequest(request, policy, now) {
  const required = [
    "protocol_version", "message_type", "request_id", "issued_at", "expires_at",
    "principal", "action", "target", "scope", "policy_version",
  ];
  if (!exactKeys(request, required, ["provenance_ref"])) return "REQUEST_INVALID";
  if (request.protocol_version !== PROTOCOL_VERSION ||
      request.message_type !== "authorization_request" ||
      typeof request.request_id !== "string" || !UUID_V4.test(request.request_id)) return "REQUEST_INVALID";
  const limits = { principal: 1024, action: 256, target: 512, scope: 512, policy_version: 128 };
  for (const [field, max] of Object.entries(limits)) {
    if (!validText(request[field], max)) return "REQUEST_INVALID";
  }
  if (Object.hasOwn(request, "provenance_ref") &&
      (typeof request.provenance_ref !== "string" ||
       codePointLength(request.provenance_ref) > 2048 ||
       hasUnpairedSurrogate(request.provenance_ref))) return "REQUEST_INVALID";
  if (request.policy_version !== policy.version) return "POLICY_VERSION_MISMATCH";
  const issued = timestampMicros(request.issued_at);
  const expires = timestampMicros(request.expires_at);
  if (issued === null || expires === null) return "REQUEST_INVALID";
  if (expires <= issued) return "INVALID_VALIDITY_WINDOW";
  if (!(now instanceof Date) || !Number.isFinite(now.getTime())) return "CLOCK_INVALID";
  const nowMicros = BigInt(now.getTime()) * 1000n;
  if (nowMicros < issued) return "NOT_YET_VALID";
  if (nowMicros >= expires) return "EXPIRED";
  return null;
}

// Evaluate one parsed v1.0.0 policy and complete authorization request envelope.
// The principal must already have been derived by a trusted identity adapter.
export function evaluate(policy, request, now = new Date()) {
  const version = policy && typeof policy.version === "string" ? policy.version : "UNKNOWN";
  if (!policy || typeof policy !== "object" || Array.isArray(policy) || !validatePolicy(policy)) {
    return deny("POLICY_INVALID", version);
  }
  if (!request || typeof request !== "object" || Array.isArray(request)) {
    return deny("REQUEST_INVALID", version);
  }
  const failure = validateRequest(request, policy, now);
  if (failure) return deny(failure, version);

  let allow = false;
  let review = false;
  for (const rule of policy.rules) {
    if (rule.principals.includes(request.principal) &&
        rule.actions.includes(request.action) &&
        rule.targets.includes(request.target) &&
        rule.scopes.includes(request.scope)) {
      if (rule.effect === "DENY") return deny("EXPLICIT_DENY", version);
      if (rule.effect === "REVIEW_REQUIRED") review = true;
      if (rule.effect === "ALLOW") allow = true;
    }
  }
  if (review) return { decision: "REVIEW_REQUIRED", reason_code: "APPROVAL_REQUIRED", policy_version: version };
  if (allow) return { decision: "ALLOW", reason_code: "EXPLICIT_MATCH", policy_version: version };
  return deny("NO_MATCH", version);
}

// Strict raw-document entry point. Malformed policy/request documents fail closed.
export function evaluateJSON(policyInput, requestInput, now = new Date()) {
  let policy;
  try {
    policy = parseStrictJSON(policyInput, MAX_POLICY_BYTES);
  } catch {
    return deny("POLICY_INVALID", "UNKNOWN");
  }
  const version = typeof policy.version === "string" ? policy.version : "UNKNOWN";
  if (!validatePolicy(policy)) return deny("POLICY_INVALID", version);
  let request;
  try {
    request = parseStrictJSON(requestInput, MAX_REQUEST_BYTES);
  } catch {
    return deny("REQUEST_INVALID", version);
  }
  return evaluate(policy, request, now);
}

export const limits = Object.freeze({
  maxPolicyBytes: MAX_POLICY_BYTES,
  maxRequestBytes: MAX_REQUEST_BYTES,
  maxJsonDepth: MAX_JSON_DEPTH,
  maxRules: MAX_RULES,
  maxSelectors: MAX_SELECTORS,
});
