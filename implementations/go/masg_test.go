package masg

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"testing"
	"time"
)

type vector struct {
	VectorVersion string   `json:"vector_version"`
	VectorID      string   `json:"vector_id"`
	Category      string   `json:"category"`
	Description   string   `json:"description"`
	Policy        Policy   `json:"policy"`
	Request       Request  `json:"request"`
	Limitations   []string `json:"limitations"`
	Expected struct {
		Decision   string `json:"decision"`
		ReasonCode string `json:"reason_code"`
	} `json:"expected"`
}

func fixedClock() time.Time {
	return time.Date(2026, 11, 10, 12, 0, 30, 0, time.UTC)
}

func TestPortableV100Vectors(t *testing.T) {
	raw, err := os.ReadFile("../../vectors/v1.0.0/decision-vectors.json")
	if err != nil {
		t.Fatal(err)
	}
	var vectors []vector
	if err := decodeUniqueJSON(raw, &vectors, maxVectorJSONBytes); err != nil {
		t.Fatalf("decode shared vectors: %v", err)
	}
	if len(vectors) < 8 {
		t.Fatalf("expected at least eight shared vectors, got %d", len(vectors))
	}
	for _, testVector := range vectors {
		t.Run(testVector.VectorID, func(t *testing.T) {
			got := Evaluate(testVector.Policy, testVector.Request, fixedClock())
			if got.Decision != testVector.Expected.Decision {
				t.Fatalf("decision = %s, want %s", got.Decision, testVector.Expected.Decision)
			}
			if got.ReasonCode != testVector.Expected.ReasonCode {
				t.Fatalf("reason = %s, want %s", got.ReasonCode, testVector.Expected.ReasonCode)
			}
		})
	}
}

func TestSharedParserNegativeVectors(t *testing.T) {
	raw, err := os.ReadFile("../../vectors/v1.0.0/parser-negative-vectors.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixtures []struct {
		FixtureID string `json:"fixture_id"`
		PolicyHex string `json:"policy_json_hex"`
		RequestHex string `json:"request_json_hex"`
		ExpectedReason string `json:"expected_reason_code"`
	}
	if err := json.Unmarshal(raw, &fixtures); err != nil {
		t.Fatal(err)
	}
	if len(fixtures) < 18 {
		t.Fatalf("expected at least eighteen shared parser fixtures, got %d", len(fixtures))
	}
	now := fixedClock()
	for _, fixture := range fixtures {
		t.Run(fixture.FixtureID, func(t *testing.T) {
			policy, err := hex.DecodeString(fixture.PolicyHex)
			if err != nil { t.Fatal(err) }
			request, err := hex.DecodeString(fixture.RequestHex)
			if err != nil { t.Fatal(err) }
			got := EvaluateJSON(policy, request, now)
			if got.ReasonCode != fixture.ExpectedReason {
				t.Fatalf("reason = %s, want %s", got.ReasonCode, fixture.ExpectedReason)
			}
			if got.Decision != "DENY" {
				t.Fatalf("malformed input did not deny: %+v", got)
			}
		})
	}
}

func TestDuplicateJSONKeysFailClosed(t *testing.T) {
	policy := []byte(`{"version":"p1","default_effect":"DENY","rules":[]}`)
	request := []byte(`{"protocol_version":"1.0.0","protocol_version":"1.0.0"}`)
	got := EvaluateJSON(policy, request, fixedClock())
	if got.Decision != "DENY" || got.ReasonCode != "REQUEST_INVALID" {
		t.Fatalf("duplicate key did not fail closed: %+v", got)
	}
}

func TestInvalidUTF8FailsClosed(t *testing.T) {
	policy := []byte(`{"version":"p1","default_effect":"DENY","rules":[]}`)
	request := []byte{0xff, 0xfe, '{', '}'}
	got := EvaluateJSON(policy, request, fixedClock())
	if got.Decision != "DENY" || got.ReasonCode != "REQUEST_INVALID" {
		t.Fatalf("invalid UTF-8 did not fail closed: %+v", got)
	}
}

func TestUnknownRequestFieldFailsClosed(t *testing.T) {
	policy := []byte(`{"version":"p1","default_effect":"DENY","rules":[]}`)
	request := Request{
		ProtocolVersion: ProtocolVersion,
		MessageType: "authorization_request",
		RequestID: "550e8400-e29b-41d4-a716-446655440000",
		IssuedAt: "2026-11-10T12:00:00Z",
		ExpiresAt: "2026-11-10T12:01:00Z",
		Principal: "agent:reader", Action: "read", Target: "reports:weekly",
		Scope: "summary", PolicyVersion: "p1",
	}
	raw, _ := json.Marshal(request)
	var fields map[string]any
	_ = json.Unmarshal(raw, &fields)
	fields["unreviewed_security_field"] = true
	unknown, _ := json.Marshal(fields)
	got := EvaluateJSON(policy, unknown, fixedClock())
	if got.Decision != "DENY" || got.ReasonCode != "REQUEST_INVALID" {
		t.Fatalf("unknown field did not fail closed: %+v", got)
	}
}

func TestPolicyMustDefaultToDeny(t *testing.T) {
	policy := Policy{Version: "p1", DefaultEffect: "ALLOW"}
	request := Request{ProtocolVersion: ProtocolVersion}
	got := Evaluate(policy, request, fixedClock())
	if got.Decision != "DENY" || got.ReasonCode != "POLICY_INVALID" {
		t.Fatalf("unsafe policy did not fail closed: %+v", got)
	}
}

func TestExpiredRequestDenied(t *testing.T) {
	policy := Policy{Version: "p1", DefaultEffect: "DENY", Rules: []Rule{}}
	request := Request{
		ProtocolVersion: ProtocolVersion, MessageType: "authorization_request",
		RequestID: "550e8400-e29b-41d4-a716-446655440000",
		IssuedAt: "2026-11-10T12:00:00Z", ExpiresAt: "2026-11-10T12:00:20Z",
		Principal: "agent:reader", Action: "read", Target: "reports:weekly",
		Scope: "summary", PolicyVersion: "p1",
	}
	got := Evaluate(policy, request, fixedClock())
	if got.Decision != "DENY" || got.ReasonCode != "EXPIRED" {
		t.Fatalf("expired request did not fail closed: %+v", got)
	}
}

func TestTimestampPrecisionMatchesProtocol(t *testing.T) {
	policy := Policy{
		Version: "p1", DefaultEffect: "DENY",
		Rules: []Rule{{
			ID: "allow-read", Principals: []string{"agent:reader"},
			Actions: []string{"read"}, Targets: []string{"reports:weekly"},
			Scopes: []string{"summary"}, Effect: "ALLOW",
		}},
	}
	request := Request{
		ProtocolVersion: ProtocolVersion, MessageType: "authorization_request",
		RequestID: "550e8400-e29b-41d4-a716-446655440008",
		IssuedAt: "2026-11-10T12:00:00.123456Z",
		ExpiresAt: "2026-11-10T12:01:00.123456Z",
		Principal: "agent:reader", Action: "read", Target: "reports:weekly",
		Scope: "summary", PolicyVersion: "p1",
	}
	if got := Evaluate(policy, request, fixedClock()); got.Decision != "ALLOW" {
		t.Fatalf("six fractional digits should be accepted: %+v", got)
	}
	request.IssuedAt = "2026-11-10T12:00:00.1234567Z"
	if got := Evaluate(policy, request, fixedClock()); got.ReasonCode != "REQUEST_INVALID" {
		t.Fatalf("seven fractional digits must be rejected: %+v", got)
	}
	request.IssuedAt = "2026-11-10T12:00:00-00:00"
	if got := Evaluate(policy, request, fixedClock()); got.ReasonCode != "REQUEST_INVALID" {
		t.Fatalf("unknown local offset must be rejected: %+v", got)
	}
}

func TestUnicodeLimitsCountCodePoints(t *testing.T) {
	if !validText(strings.Repeat("é", 1024), 1024) {
		t.Fatal("1024 Unicode code points should fit the principal limit")
	}
	if validText(strings.Repeat("é", 1025), 1024) {
		t.Fatal("1025 Unicode code points must exceed the principal limit")
	}
}

func TestPolicyLimitsMatchSchema(t *testing.T) {
	base := Policy{
		Version: "p1", DefaultEffect: "DENY",
		Rules: []Rule{{
			ID: "rule-1", Principals: []string{"agent:reader"},
			Actions: []string{"read"}, Targets: []string{"reports:weekly"},
			Scopes: []string{"summary"}, Effect: "ALLOW",
		}},
	}
	if err := validatePolicy(base); err != nil {
		t.Fatalf("valid schema policy rejected: %v", err)
	}
	tooLongAction := base
	tooLongAction.Rules = append([]Rule(nil), base.Rules...)
	tooLongAction.Rules[0].Actions = []string{strings.Repeat("x", 257)}
	if err := validatePolicy(tooLongAction); err == nil {
		t.Fatal("action exceeding 256 code points must be rejected")
	}
	tooManySelectors := base
	tooManySelectors.Rules = append([]Rule(nil), base.Rules...)
	tooManySelectors.Rules[0].Principals = make([]string, 129)
	for i := range tooManySelectors.Rules[0].Principals {
		tooManySelectors.Rules[0].Principals[i] = fmt.Sprintf("agent:%d", i)
	}
	if err := validatePolicy(tooManySelectors); err == nil {
		t.Fatal("more than 128 selectors must be rejected")
	}
	if err := validatePolicy(Policy{Version: "p1", DefaultEffect: "DENY"}); err == nil {
		t.Fatal("missing rules array must be rejected")
	}
}

func TestExcessiveJSONNestingFailsClosed(t *testing.T) {
	policy := []byte(`{"version":"p1","default_effect":"DENY","rules":[]}`)
	request := []byte(`{"x":` + strings.Repeat("[", 33) + "0" + strings.Repeat("]", 33) + "}")
	got := EvaluateJSON(policy, request, fixedClock())
	if got.Decision != "DENY" || got.ReasonCode != "REQUEST_INVALID" {
		t.Fatalf("excessive nesting did not fail closed: %+v", got)
	}
}

func TestJSONDepthBoundary(t *testing.T) {
	var value any
	atLimit := []byte(strings.Repeat("[", 32) + "0" + strings.Repeat("]", 32))
	if err := decodeUniqueJSON(atLimit, &value, maxVectorJSONBytes); err != nil {
		t.Fatalf("32 container levels should be accepted: %v", err)
	}
	overLimit := []byte(strings.Repeat("[", 33) + "0" + strings.Repeat("]", 33))
	if err := decodeUniqueJSON(overLimit, &value, maxVectorJSONBytes); err == nil {
		t.Fatal("33 container levels must be rejected")
	}
}
