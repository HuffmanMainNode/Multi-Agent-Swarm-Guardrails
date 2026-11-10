//! MASG v1.0.0 independent Rust reference evaluator.
//!
//! This crate implements strict JSON parsing and the portable policy-decision
//! subset. It does not authenticate principals or mediate protected side effects.

use std::collections::{BTreeMap, BTreeSet};

const MAX_POLICY_BYTES: usize = 1_048_576;
const MAX_REQUEST_BYTES: usize = 65_536;
#[cfg(test)]
const MAX_VECTOR_BYTES: usize = 1_048_576;
const MAX_JSON_DEPTH: usize = 32;
const MAX_RULES: usize = 1_000;
const MAX_SELECTORS: usize = 128;

#[derive(Debug, Clone, PartialEq)]
enum JsonValue {
    Null,
    Bool,
    Number,
    String(String),
    Array(Vec<JsonValue>),
    Object(BTreeMap<String, JsonValue>),
}

struct JsonParser<'a> {
    input: &'a str,
    position: usize,
}

impl<'a> JsonParser<'a> {
    fn new(input: &'a str) -> Self {
        Self { input, position: 0 }
    }

    fn parse(mut self) -> std::result::Result<JsonValue, String> {
        let value = self.parse_value(0)?;
        self.skip_whitespace();
        if self.position != self.input.len() {
            return Err("trailing JSON data".to_string());
        }
        Ok(value)
    }

    fn parse_value(&mut self, depth: usize) -> std::result::Result<JsonValue, String> {
        self.skip_whitespace();
        match self.peek() {
            Some(b'{') => self.parse_object(depth + 1),
            Some(b'[') => self.parse_array(depth + 1),
            Some(b'"') => self.parse_string().map(JsonValue::String),
            Some(b't') => {
                self.consume_literal("true")?;
                Ok(JsonValue::Bool)
            }
            Some(b'f') => {
                self.consume_literal("false")?;
                Ok(JsonValue::Bool)
            }
            Some(b'n') => {
                self.consume_literal("null")?;
                Ok(JsonValue::Null)
            }
            Some(b'-' | b'0'..=b'9') => {
                self.parse_number()?;
                Ok(JsonValue::Number)
            }
            _ => Err("invalid JSON value".to_string()),
        }
    }

    fn parse_object(&mut self, depth: usize) -> std::result::Result<JsonValue, String> {
        if depth > MAX_JSON_DEPTH {
            return Err("JSON nesting too deep".to_string());
        }
        self.expect_byte(b'{')?;
        self.skip_whitespace();
        let mut values = BTreeMap::new();
        if self.peek() == Some(b'}') {
            self.position += 1;
            return Ok(JsonValue::Object(values));
        }
        loop {
            self.skip_whitespace();
            if self.peek() != Some(b'"') {
                return Err("object key must be a string".to_string());
            }
            let key = self.parse_string()?;
            if values.contains_key(&key) {
                return Err(format!("duplicate JSON object key: {key}"));
            }
            self.skip_whitespace();
            self.expect_byte(b':')?;
            let value = self.parse_value(depth)?;
            values.insert(key, value);
            self.skip_whitespace();
            match self.peek() {
                Some(b',') => self.position += 1,
                Some(b'}') => {
                    self.position += 1;
                    break;
                }
                _ => return Err("invalid object separator".to_string()),
            }
        }
        Ok(JsonValue::Object(values))
    }

    fn parse_array(&mut self, depth: usize) -> std::result::Result<JsonValue, String> {
        if depth > MAX_JSON_DEPTH {
            return Err("JSON nesting too deep".to_string());
        }
        self.expect_byte(b'[')?;
        self.skip_whitespace();
        let mut values = Vec::new();
        if self.peek() == Some(b']') {
            self.position += 1;
            return Ok(JsonValue::Array(values));
        }
        loop {
            values.push(self.parse_value(depth)?);
            self.skip_whitespace();
            match self.peek() {
                Some(b',') => self.position += 1,
                Some(b']') => {
                    self.position += 1;
                    break;
                }
                _ => return Err("invalid array separator".to_string()),
            }
        }
        Ok(JsonValue::Array(values))
    }

    fn parse_string(&mut self) -> std::result::Result<String, String> {
        self.expect_byte(b'"')?;
        let mut output = String::new();
        while let Some(byte) = self.peek() {
            match byte {
                b'"' => {
                    self.position += 1;
                    return Ok(output);
                }
                b'\\' => {
                    self.position += 1;
                    let escaped = self
                        .peek()
                        .ok_or_else(|| "incomplete string escape".to_string())?;
                    self.position += 1;
                    match escaped {
                        b'"' => output.push('"'),
                        b'\\' => output.push('\\'),
                        b'/' => output.push('/'),
                        b'b' => output.push('\u{0008}'),
                        b'f' => output.push('\u{000C}'),
                        b'n' => output.push('\n'),
                        b'r' => output.push('\r'),
                        b't' => output.push('\t'),
                        b'u' => {
                            let first = self.parse_hex4()?;
                            let codepoint = if (0xD800..=0xDBFF).contains(&first) {
                                if self.peek() != Some(b'\\')
                                    || self.input.as_bytes().get(self.position + 1) != Some(&b'u')
                                {
                                    return Err("unpaired high surrogate".to_string());
                                }
                                self.position += 2;
                                let second = self.parse_hex4()?;
                                if !(0xDC00..=0xDFFF).contains(&second) {
                                    return Err("invalid low surrogate".to_string());
                                }
                                0x10000
                                    + (((first - 0xD800) as u32) << 10)
                                    + (second - 0xDC00) as u32
                            } else if (0xDC00..=0xDFFF).contains(&first) {
                                return Err("unpaired low surrogate".to_string());
                            } else {
                                first as u32
                            };
                            let character = char::from_u32(codepoint)
                                .ok_or_else(|| "invalid Unicode scalar".to_string())?;
                            output.push(character);
                        }
                        _ => return Err("invalid string escape".to_string()),
                    }
                }
                0x00..=0x1F => return Err("unescaped control character".to_string()),
                0x20..=0x7F => {
                    output.push(byte as char);
                    self.position += 1;
                }
                _ => {
                    let character = self.input[self.position..]
                        .chars()
                        .next()
                        .ok_or_else(|| "invalid UTF-8 string".to_string())?;
                    output.push(character);
                    self.position += character.len_utf8();
                }
            }
        }
        Err("unterminated JSON string".to_string())
    }

    fn parse_hex4(&mut self) -> std::result::Result<u16, String> {
        let mut value = 0u16;
        for _ in 0..4 {
            let byte = self
                .peek()
                .ok_or_else(|| "incomplete Unicode escape".to_string())?;
            self.position += 1;
            let digit = match byte {
                b'0'..=b'9' => (byte - b'0') as u16,
                b'a'..=b'f' => (byte - b'a' + 10) as u16,
                b'A'..=b'F' => (byte - b'A' + 10) as u16,
                _ => return Err("invalid Unicode escape".to_string()),
            };
            value = (value << 4) | digit;
        }
        Ok(value)
    }

    fn parse_number(&mut self) -> std::result::Result<(), String> {
        if self.peek() == Some(b'-') {
            self.position += 1;
        }
        match self.peek() {
            Some(b'0') => {
                self.position += 1;
                if matches!(self.peek(), Some(b'0'..=b'9')) {
                    return Err("leading zero in JSON number".to_string());
                }
            }
            Some(b'1'..=b'9') => {
                self.position += 1;
                while matches!(self.peek(), Some(b'0'..=b'9')) {
                    self.position += 1;
                }
            }
            _ => return Err("invalid JSON number".to_string()),
        }
        if self.peek() == Some(b'.') {
            self.position += 1;
            let fraction_start = self.position;
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.position += 1;
            }
            if self.position == fraction_start {
                return Err("invalid JSON fraction".to_string());
            }
        }
        if matches!(self.peek(), Some(b'e' | b'E')) {
            self.position += 1;
            if matches!(self.peek(), Some(b'+' | b'-')) {
                self.position += 1;
            }
            let exponent_start = self.position;
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.position += 1;
            }
            if self.position == exponent_start {
                return Err("invalid JSON exponent".to_string());
            }
        }
        Ok(())
    }

    fn consume_literal(&mut self, literal: &str) -> std::result::Result<(), String> {
        if self.input[self.position..].starts_with(literal) {
            self.position += literal.len();
            Ok(())
        } else {
            Err("invalid JSON literal".to_string())
        }
    }

    fn expect_byte(&mut self, expected: u8) -> std::result::Result<(), String> {
        if self.peek() == Some(expected) {
            self.position += 1;
            Ok(())
        } else {
            Err("unexpected JSON token".to_string())
        }
    }

    fn skip_whitespace(&mut self) {
        while matches!(self.peek(), Some(b' ' | b'\t' | b'\n' | b'\r')) {
            self.position += 1;
        }
    }

    fn peek(&self) -> Option<u8> {
        self.input.as_bytes().get(self.position).copied()
    }
}

fn parse_json(raw: &[u8], max_bytes: usize) -> std::result::Result<JsonValue, String> {
    if raw.is_empty() || raw.len() > max_bytes {
        return Err("JSON size invalid".to_string());
    }
    let input = std::str::from_utf8(raw).map_err(|_| "invalid UTF-8".to_string())?;
    JsonParser::new(input).parse()
}

fn as_object(value: &JsonValue) -> std::result::Result<&BTreeMap<String, JsonValue>, String> {
    match value {
        JsonValue::Object(object) => Ok(object),
        _ => Err("expected JSON object".to_string()),
    }
}

fn as_array(value: &JsonValue) -> std::result::Result<&[JsonValue], String> {
    match value {
        JsonValue::Array(array) => Ok(array),
        _ => Err("expected JSON array".to_string()),
    }
}

fn as_string(value: &JsonValue, field: &str) -> std::result::Result<String, String> {
    match value {
        JsonValue::String(string) => Ok(string.clone()),
        _ => Err(format!("{field} must be a string")),
    }
}

fn valid_text(value: &str, max_chars: usize) -> bool {
    !value.trim().is_empty() && value.chars().count() <= max_chars
}

fn exact_keys(object: &BTreeMap<String, JsonValue>, required: &[&str], optional: &[&str]) -> bool {
    required.iter().all(|key| object.contains_key(*key))
        && object
            .keys()
            .all(|key| required.contains(&key.as_str()) || optional.contains(&key.as_str()))
}

fn parse_selectors(
    object: &BTreeMap<String, JsonValue>,
    field: &str,
    max_chars: usize,
) -> std::result::Result<Vec<String>, String> {
    let values = as_array(
        object
            .get(field)
            .ok_or_else(|| format!("missing {field}"))?,
    )?;
    if values.is_empty() || values.len() > MAX_SELECTORS {
        return Err(format!("{field} selector count invalid"));
    }
    let mut output = Vec::with_capacity(values.len());
    let mut unique = BTreeSet::new();
    for item in values {
        let value = as_string(item, field)?;
        if !valid_text(&value, max_chars) || !unique.insert(value.clone()) {
            return Err(format!("{field} selector invalid or duplicated"));
        }
        output.push(value);
    }
    Ok(output)
}

#[derive(Debug)]
struct Rule {
    principals: Vec<String>,
    actions: Vec<String>,
    targets: Vec<String>,
    scopes: Vec<String>,
    effect: String,
}

#[derive(Debug)]
struct Policy {
    version: String,
    rules: Vec<Rule>,
}

#[derive(Debug)]
struct Request {
    issued_at: String,
    expires_at: String,
    principal: String,
    action: String,
    target: String,
    scope: String,
    policy_version: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DecisionResult {
    pub decision: String,
    pub reason_code: String,
    pub policy_version: String,
}

fn deny(reason: &str, version: &str) -> DecisionResult {
    DecisionResult {
        decision: "DENY".to_string(),
        reason_code: reason.to_string(),
        policy_version: version.to_string(),
    }
}

fn parse_policy(value: &JsonValue) -> std::result::Result<Policy, String> {
    let object = as_object(value)?;
    if !exact_keys(object, &["version", "default_effect", "rules"], &[]) {
        return Err("policy fields invalid".to_string());
    }
    let version = as_string(&object["version"], "version")?;
    if !valid_text(&version, 128) {
        return Err("policy version invalid".to_string());
    }
    if as_string(&object["default_effect"], "default_effect")? != "DENY" {
        return Err("policy must default to DENY".to_string());
    }
    let rules_value = as_array(&object["rules"])?;
    if rules_value.len() > MAX_RULES {
        return Err("too many policy rules".to_string());
    }
    let mut rules = Vec::with_capacity(rules_value.len());
    for rule_value in rules_value {
        let rule = as_object(rule_value)?;
        if !exact_keys(
            rule,
            &["id", "principals", "actions", "targets", "scopes", "effect"],
            &[],
        ) {
            return Err("policy rule fields invalid".to_string());
        }
        let id = as_string(&rule["id"], "rule.id")?;
        if !valid_text(&id, 128) {
            return Err("policy rule ID invalid".to_string());
        }
        let principals = parse_selectors(rule, "principals", 1024)?;
        let actions = parse_selectors(rule, "actions", 256)?;
        let targets = parse_selectors(rule, "targets", 512)?;
        let scopes = parse_selectors(rule, "scopes", 512)?;
        let effect = as_string(&rule["effect"], "effect")?;
        if !matches!(effect.as_str(), "ALLOW" | "DENY" | "REVIEW_REQUIRED") {
            return Err("policy effect invalid".to_string());
        }
        rules.push(Rule {
            principals,
            actions,
            targets,
            scopes,
            effect,
        });
    }
    Ok(Policy { version, rules })
}

fn valid_uuid_v4(value: &str) -> bool {
    let bytes = value.as_bytes();
    if bytes.len() != 36
        || bytes[8] != b'-'
        || bytes[13] != b'-'
        || bytes[18] != b'-'
        || bytes[23] != b'-'
    {
        return false;
    }
    if bytes[14] != b'4' || !matches!(bytes[19], b'8' | b'9' | b'a' | b'b') {
        return false;
    }
    bytes.iter().enumerate().all(|(index, byte)| {
        if matches!(index, 8 | 13 | 18 | 23) {
            *byte == b'-'
        } else {
            byte.is_ascii_digit() || (b'a'..=b'f').contains(byte)
        }
    })
}

fn parse_two_digits(bytes: &[u8], start: usize) -> Option<i64> {
    let first = *bytes.get(start)?;
    let second = *bytes.get(start + 1)?;
    if !first.is_ascii_digit() || !second.is_ascii_digit() {
        return None;
    }
    Some(((first - b'0') * 10 + (second - b'0')) as i64)
}

fn parse_four_digits(bytes: &[u8], start: usize) -> Option<i64> {
    let mut value = 0i64;
    for offset in 0..4 {
        let byte = *bytes.get(start + offset)?;
        if !byte.is_ascii_digit() {
            return None;
        }
        value = value * 10 + (byte - b'0') as i64;
    }
    Some(value)
}

fn days_from_civil(year: i64, month: i64, day: i64) -> i64 {
    let adjusted_year = year - if month <= 2 { 1 } else { 0 };
    let era = if adjusted_year >= 0 {
        adjusted_year
    } else {
        adjusted_year - 399
    } / 400;
    let year_of_era = adjusted_year - era * 400;
    let adjusted_month = month + if month > 2 { -3 } else { 9 };
    let day_of_year = (153 * adjusted_month + 2) / 5 + day - 1;
    let day_of_era = year_of_era * 365 + year_of_era / 4 - year_of_era / 100 + day_of_year;
    era * 146097 + day_of_era - 719468
}

fn parse_timestamp(value: &str) -> Option<i128> {
    let bytes = value.as_bytes();
    if bytes.len() < 20 || bytes.len() > 32 {
        return None;
    }
    if bytes[4] != b'-'
        || bytes[7] != b'-'
        || bytes[10] != b'T'
        || bytes[13] != b':'
        || bytes[16] != b':'
    {
        return None;
    }
    let year = parse_four_digits(bytes, 0)?;
    let month = parse_two_digits(bytes, 5)?;
    let day = parse_two_digits(bytes, 8)?;
    let hour = parse_two_digits(bytes, 11)?;
    let minute = parse_two_digits(bytes, 14)?;
    let second = parse_two_digits(bytes, 17)?;
    if year == 0
        || !(1..=12).contains(&month)
        || !(0..=23).contains(&hour)
        || !(0..=59).contains(&minute)
        || !(0..=59).contains(&second)
    {
        return None;
    }
    let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    let month_days = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 if leap => 29,
        2 => 28,
        _ => return None,
    };
    if day < 1 || day > month_days {
        return None;
    }

    let mut position = 19;
    let mut fractional_micros = 0i128;
    if bytes.get(position) == Some(&b'.') {
        position += 1;
        let start = position;
        while position < bytes.len() && bytes[position].is_ascii_digit() {
            position += 1;
        }
        let digits = position - start;
        if !(1..=6).contains(&digits) {
            return None;
        }
        let mut fraction = 0i128;
        for byte in &bytes[start..position] {
            fraction = fraction * 10 + (byte - b'0') as i128;
        }
        for _ in digits..6 {
            fraction *= 10;
        }
        fractional_micros = fraction;
    }

    let mut offset_seconds = 0i64;
    match bytes.get(position).copied()? {
        b'Z' if position + 1 == bytes.len() => {}
        sign @ (b'+' | b'-') if position + 6 == bytes.len() => {
            if bytes[position + 3] != b':' {
                return None;
            }
            let offset_hour = parse_two_digits(bytes, position + 1)?;
            let offset_minute = parse_two_digits(bytes, position + 4)?;
            if offset_hour > 23 || offset_minute > 59 {
                return None;
            }
            if sign == b'-' && offset_hour == 0 && offset_minute == 0 {
                return None;
            }
            let magnitude = offset_hour * 3600 + offset_minute * 60;
            offset_seconds = if sign == b'+' { magnitude } else { -magnitude };
        }
        _ => return None,
    }

    let days = days_from_civil(year, month, day);
    let local_seconds = days * 86_400 + hour * 3_600 + minute * 60 + second;
    Some((local_seconds - offset_seconds) as i128 * 1_000_000 + fractional_micros)
}

fn parse_request(value: &JsonValue) -> std::result::Result<Request, String> {
    let object = as_object(value)?;
    if !exact_keys(
        object,
        &[
            "protocol_version",
            "message_type",
            "request_id",
            "issued_at",
            "expires_at",
            "principal",
            "action",
            "target",
            "scope",
            "policy_version",
        ],
        &["provenance_ref"],
    ) {
        return Err("request fields invalid".to_string());
    }
    if as_string(&object["protocol_version"], "protocol_version")? != "1.0.0"
        || as_string(&object["message_type"], "message_type")? != "authorization_request"
    {
        return Err("protocol version or message type unsupported".to_string());
    }
    let request_id = as_string(&object["request_id"], "request_id")?;
    if !valid_uuid_v4(&request_id) {
        return Err("request ID must be canonical lowercase UUIDv4".to_string());
    }
    let principal = as_string(&object["principal"], "principal")?;
    let action = as_string(&object["action"], "action")?;
    let target = as_string(&object["target"], "target")?;
    let scope = as_string(&object["scope"], "scope")?;
    let policy_version = as_string(&object["policy_version"], "policy_version")?;
    if !valid_text(&principal, 1024)
        || !valid_text(&action, 256)
        || !valid_text(&target, 512)
        || !valid_text(&scope, 512)
        || !valid_text(&policy_version, 128)
    {
        return Err("request field length or value invalid".to_string());
    }
    if let Some(provenance) = object.get("provenance_ref") {
        let provenance = as_string(provenance, "provenance_ref")?;
        if provenance.chars().count() > 2048 {
            return Err("provenance reference too long".to_string());
        }
    }
    let issued_at = as_string(&object["issued_at"], "issued_at")?;
    let expires_at = as_string(&object["expires_at"], "expires_at")?;
    Ok(Request {
        issued_at,
        expires_at,
        principal,
        action,
        target,
        scope,
        policy_version,
    })
}

fn evaluate_values(
    policy_value: &JsonValue,
    request_value: &JsonValue,
    now_unix_micros: i128,
) -> DecisionResult {
    let version = as_object(policy_value)
        .ok()
        .and_then(|object| object.get("version"))
        .and_then(|value| match value {
            JsonValue::String(version) => Some(version.clone()),
            _ => None,
        })
        .unwrap_or_else(|| "UNKNOWN".to_string());
    let policy = match parse_policy(policy_value) {
        Ok(policy) => policy,
        Err(_) => return deny("POLICY_INVALID", &version),
    };
    let request = match parse_request(request_value) {
        Ok(request) => request,
        Err(_) => return deny("REQUEST_INVALID", &policy.version),
    };
    if request.policy_version != policy.version {
        return deny("POLICY_VERSION_MISMATCH", &policy.version);
    }
    let issued = match parse_timestamp(&request.issued_at) {
        Some(value) => value,
        None => return deny("REQUEST_INVALID", &policy.version),
    };
    let expires = match parse_timestamp(&request.expires_at) {
        Some(value) => value,
        None => return deny("REQUEST_INVALID", &policy.version),
    };
    if expires <= issued {
        return deny("INVALID_VALIDITY_WINDOW", &policy.version);
    }
    if now_unix_micros < issued {
        return deny("NOT_YET_VALID", &policy.version);
    }
    if now_unix_micros >= expires {
        return deny("EXPIRED", &policy.version);
    }

    let mut allow = false;
    let mut review = false;
    for rule in &policy.rules {
        if rule
            .principals
            .iter()
            .any(|value| value == &request.principal)
            && rule.actions.iter().any(|value| value == &request.action)
            && rule.targets.iter().any(|value| value == &request.target)
            && rule.scopes.iter().any(|value| value == &request.scope)
        {
            match rule.effect.as_str() {
                "DENY" => return deny("EXPLICIT_DENY", &policy.version),
                "REVIEW_REQUIRED" => review = true,
                "ALLOW" => allow = true,
                _ => return deny("POLICY_INVALID", &policy.version),
            }
        }
    }
    if review {
        DecisionResult {
            decision: "REVIEW_REQUIRED".to_string(),
            reason_code: "APPROVAL_REQUIRED".to_string(),
            policy_version: policy.version,
        }
    } else if allow {
        DecisionResult {
            decision: "ALLOW".to_string(),
            reason_code: "EXPLICIT_MATCH".to_string(),
            policy_version: policy.version,
        }
    } else {
        deny("NO_MATCH", &policy.version)
    }
}

/// Evaluate strict UTF-8 JSON policy and v1.0.0 authorization request documents.
///
/// The caller supplies now_unix_micros. This crate does not provide trusted time,
/// authenticate the principal, consume replay state, or execute tools.
pub fn evaluate_json(
    policy_json: &[u8],
    request_json: &[u8],
    now_unix_micros: i128,
) -> DecisionResult {
    let policy_value = match parse_json(policy_json, MAX_POLICY_BYTES) {
        Ok(value) => value,
        Err(_) => return deny("POLICY_INVALID", "UNKNOWN"),
    };
    let version = as_object(&policy_value)
        .ok()
        .and_then(|object| object.get("version"))
        .and_then(|value| match value {
            JsonValue::String(version) => Some(version.as_str()),
            _ => None,
        })
        .unwrap_or("UNKNOWN")
        .to_string();
    let request_value = match parse_json(request_json, MAX_REQUEST_BYTES) {
        Ok(value) => value,
        Err(_) => return deny("REQUEST_INVALID", &version),
    };
    evaluate_values(&policy_value, &request_value, now_unix_micros)
}

/// Alias for the primary evaluator.
pub fn evaluate(policy_json: &[u8], request_json: &[u8], now_unix_micros: i128) -> DecisionResult {
    evaluate_json(policy_json, request_json, now_unix_micros)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixed_now() -> i128 {
        parse_timestamp("2026-11-10T12:00:30Z").unwrap()
    }

    #[test]
    fn all_shared_v100_vectors_pass() {
        let path = format!(
            "{}/../../vectors/v1.0.0/decision-vectors.json",
            env!("CARGO_MANIFEST_DIR")
        );
        let raw = std::fs::read(path).unwrap();
        let vectors = parse_json(&raw, MAX_VECTOR_BYTES).unwrap();
        let vectors = as_array(&vectors).unwrap();
        assert!(vectors.len() >= 8);
        for vector in vectors {
            let object = as_object(vector).unwrap();
            let result = evaluate_values(&object["policy"], &object["request"], fixed_now());
            let expected = as_object(&object["expected"]).unwrap();
            assert_eq!(
                result.decision,
                as_string(&expected["decision"], "decision").unwrap(),
                "{}",
                as_string(&object["vector_id"], "vector_id").unwrap()
            );
            assert_eq!(
                result.reason_code,
                as_string(&expected["reason_code"], "reason_code").unwrap(),
                "{}",
                as_string(&object["vector_id"], "vector_id").unwrap()
            );
        }
    }

    fn decode_hex(input: &str) -> std::result::Result<Vec<u8>, String> {
        if input.len() & 1 == 1 {
            return Err("hex string has odd length".to_string());
        }
        input
            .as_bytes()
            .chunks(2)
            .map(|pair| {
                let high = (pair[0] as char)
                    .to_digit(16)
                    .ok_or_else(|| "invalid hex".to_string())?;
                let low = (pair[1] as char)
                    .to_digit(16)
                    .ok_or_else(|| "invalid hex".to_string())?;
                Ok(((high << 4) | low) as u8)
            })
            .collect()
    }

    #[test]
    fn shared_parser_negative_vectors_match() {
        let path = format!(
            "{}/../../vectors/v1.0.0/parser-negative-vectors.json",
            env!("CARGO_MANIFEST_DIR")
        );
        let raw = std::fs::read(path).unwrap();
        let fixtures = parse_json(&raw, MAX_VECTOR_BYTES).unwrap();
        let fixtures = as_array(&fixtures).unwrap();
        assert!(fixtures.len() >= 18);
        for fixture in fixtures {
            let object = as_object(fixture).unwrap();
            let policy = decode_hex(
                as_string(&object["policy_json_hex"], "policy_json_hex")
                    .unwrap()
                    .as_str(),
            )
            .unwrap();
            let request = decode_hex(
                as_string(&object["request_json_hex"], "request_json_hex")
                    .unwrap()
                    .as_str(),
            )
            .unwrap();
            let expected =
                as_string(&object["expected_reason_code"], "expected_reason_code").unwrap();
            let id = as_string(&object["fixture_id"], "fixture_id").unwrap();
            let result = evaluate_json(&policy, &request, fixed_now());
            assert_eq!(result.decision, "DENY", "{id}");
            assert_eq!(result.reason_code, expected, "{id}");
        }
    }

    #[test]
    fn duplicate_keys_fail_closed() {
        let policy = br#"{"version":"p1","default_effect":"DENY","rules":[]}"#;
        let request = br#"{"protocol_version":"1.0.0","protocol_version":"1.0.0"}"#;
        assert_eq!(
            evaluate_json(policy, request, fixed_now()).reason_code,
            "REQUEST_INVALID"
        );
    }

    #[test]
    fn invalid_utf8_fails_closed() {
        let policy = br#"{"version":"p1","default_effect":"DENY","rules":[]}"#;
        let request = [0xff, 0xfe, b'{', b'}'];
        assert_eq!(
            evaluate_json(policy, &request, fixed_now()).reason_code,
            "REQUEST_INVALID"
        );
    }

    #[test]
    fn excessive_nesting_fails_closed() {
        let policy = br#"{"version":"p1","default_effect":"DENY","rules":[]}"#;
        let mut request = b"{\"x\":".to_vec();
        request.extend(std::iter::repeat_n(b'[', 33));
        request.push(b'0');
        request.extend(std::iter::repeat_n(b']', 33));
        request.push(b'}');
        assert_eq!(
            evaluate_json(policy, &request, fixed_now()).reason_code,
            "REQUEST_INVALID"
        );
    }

    #[test]
    fn exact_json_depth_boundary_is_32_containers() {
        let at_limit = format!("{}0{}", "[".repeat(32), "]".repeat(32));
        assert!(parse_json(at_limit.as_bytes(), MAX_VECTOR_BYTES).is_ok());
        let over_limit = format!("{}0{}", "[".repeat(33), "]".repeat(33));
        assert!(parse_json(over_limit.as_bytes(), MAX_VECTOR_BYTES).is_err());
    }

    #[test]
    fn unknown_fields_fail_closed() {
        let policy = br#"{"version":"p1","default_effect":"DENY","rules":[]}"#;
        let request = br#"{"protocol_version":"1.0.0","message_type":"authorization_request","request_id":"550e8400-e29b-41d4-a716-446655440000","issued_at":"2026-11-10T12:00:00Z","expires_at":"2026-11-10T12:01:00Z","principal":"agent:reader","action":"read","target":"reports:weekly","scope":"summary","policy_version":"p1","surprise":true}"#;
        assert_eq!(
            evaluate_json(policy, request, fixed_now()).reason_code,
            "REQUEST_INVALID"
        );
    }

    #[test]
    fn timestamp_precision_and_known_offset_match_protocol() {
        assert!(parse_timestamp("2026-11-10T12:00:00.123456Z").is_some());
        assert!(parse_timestamp("2026-11-10T12:00:00.1234567Z").is_none());
        assert!(parse_timestamp("2026-11-10T12:00:00-00:00").is_none());
    }

    #[test]
    fn unicode_limits_count_code_points() {
        assert!(valid_text(&"é".repeat(1024), 1024));
        assert!(!valid_text(&"é".repeat(1025), 1024));
    }

    #[test]
    fn optional_provenance_reference_is_accepted_but_not_authority() {
        let policy = br#"{"version":"p1","default_effect":"DENY","rules":[{"id":"allow","principals":["agent:reader"],"actions":["read"],"targets":["reports:weekly"],"scopes":["summary"],"effect":"ALLOW"}]}"#;
        let request = br#"{"protocol_version":"1.0.0","message_type":"authorization_request","request_id":"550e8400-e29b-41d4-a716-446655440000","issued_at":"2026-11-10T12:00:00Z","expires_at":"2026-11-10T12:01:00Z","principal":"agent:reader","action":"read","target":"reports:weekly","scope":"summary","policy_version":"p1","provenance_ref":"sha256:abc123"}"#;
        assert_eq!(
            evaluate_json(policy, request, fixed_now()).decision,
            "ALLOW"
        );
    }
}
