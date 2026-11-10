import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { evaluate, evaluateJSON } from "./index.js";

const vectors = JSON.parse(await readFile(new URL("../../vectors/v1.0.0/decision-vectors.json", import.meta.url), "utf8"));
const parserVectors = JSON.parse(await readFile(new URL("../../vectors/v1.0.0/parser-negative-vectors.json", import.meta.url), "utf8"));
const fixedNow = new Date("2026-11-10T12:00:30.000Z");

test("all shared MASG v1.0.0 decision/time vectors pass", () => {
  assert.equal(vectors.length, 8);
  for (const vector of vectors) {
    const result = evaluate(vector.policy, vector.request, fixedNow);
    assert.equal(result.decision, vector.expected.decision, vector.vector_id);
    assert.equal(result.reason_code, vector.expected.reason_code, vector.vector_id);
  }
});

test("all shared parser-negative fixtures fail closed identically", () => {
  assert.equal(parserVectors.length, 21);
  for (const fixture of parserVectors) {
    const result = evaluateJSON(Buffer.from(fixture.policy_json_hex, "hex"), Buffer.from(fixture.request_json_hex, "hex"), fixedNow);
    assert.equal(result.decision, "DENY", fixture.fixture_id);
    assert.equal(result.reason_code, fixture.expected_reason_code, fixture.fixture_id);
  }
});

test("Unicode selector lengths use code points, not UTF-8 bytes", () => {
  const policy = {version:"unicode-1",default_effect:"DENY",rules:[{id:"unicode-allow",principals:["é".repeat(1024)],actions:["read"],targets:[vectors[0].request.target],scopes:[vectors[0].request.scope],effect:"ALLOW"}]};
  const request = {...vectors[0].request,principal:"é".repeat(1024),policy_version:"unicode-1"};
  assert.equal(evaluate(policy, request, fixedNow).decision, "ALLOW");
  request.principal = "é".repeat(1025);
  assert.equal(evaluate(policy, request, fixedNow).reason_code, "REQUEST_INVALID");
});

test("timestamp precision and unknown local offset fail closed", () => {
  const request = {...vectors[0].request,issued_at:"2026-11-10T12:00:00.1234567Z"};
  assert.equal(evaluate(vectors[0].policy, request, fixedNow).reason_code, "REQUEST_INVALID");
  request.issued_at = "2026-11-10T12:00:00-00:00";
  assert.equal(evaluate(vectors[0].policy, request, fixedNow).reason_code, "REQUEST_INVALID");
});

test("impossible RFC3339 calendar and clock values fail closed", () => {
  const request = {...vectors[0].request, expires_at:"2027-01-01T00:00:00Z"};
  for (const invalid of [
    "2026-02-30T12:00:00Z",
    "2026-02-29T12:00:00Z",
    "2026-13-01T12:00:00Z",
    "2026-04-31T12:00:00Z",
    "2026-11-10T24:00:00Z",
    "2026-11-10T12:60:00Z",
    "2026-11-10T12:00:60Z",
  ]) {
    request.issued_at = invalid;
    assert.equal(evaluate(vectors[0].policy, request, fixedNow).reason_code, "REQUEST_INVALID", invalid);
  }
});

test("valid RFC3339 leap day remains accepted", () => {
  const request = {
    ...vectors[0].request,
    issued_at:"2024-02-29T12:00:00Z",
    expires_at:"2027-01-01T00:00:00Z",
  };
  assert.equal(evaluate(vectors[0].policy, request, fixedNow).decision, "ALLOW");
});

test("strict raw JSON rejects unknown fields and excessive nesting", () => {
  const policy = JSON.stringify(vectors[0].policy);
  const request = JSON.stringify(vectors[0].request);
  assert.equal(evaluateJSON(policy, request, fixedNow).decision, "ALLOW");
  assert.equal(evaluateJSON(policy, request.slice(0,-1)+',"unknown":true}', fixedNow).reason_code, "REQUEST_INVALID");
  const tooDeep = '{"nested":' + "[".repeat(32) + "0" + "]".repeat(32) + "}";
  assert.equal(evaluateJSON(policy, tooDeep, fixedNow).reason_code, "REQUEST_INVALID");
});
