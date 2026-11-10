package masg

import (
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
