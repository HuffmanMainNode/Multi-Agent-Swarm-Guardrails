// Package masg implements the MASG v1.0.0 policy-decision reference in Go.
//
// It is deliberately an evaluator, not an identity provider, transport broker,
// sandbox, or proof that a caller's side effects are mediated.
package masg

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"regexp"
	"strings"
	"time"
	"unicode/utf8"
)

const (
	ProtocolVersion     = "1.0.0"
	maxPolicyJSONBytes  = 1_048_576
	maxRequestJSONBytes = 65_536
	maxVectorJSONBytes  = 1_048_576
	maxJSONDepth        = 32
	maxRules            = 1000
	maxSelectors        = 128
)

var uuidV4Pattern = regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`)
var rfc3339Pattern = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-](?:0\d|1\d|2[0-3]):[0-5]\d)$`)

// Policy is the language-neutral MASG decision policy document.

type Policy struct {
	Version       string `json:"version"`
	DefaultEffect string `json:"default_effect"`
	Rules         []Rule `json:"rules"`
}

// Rule is one exact-match policy rule.
type Rule struct {
	ID        string   `json:"id"`
	Principals []string `json:"principals"`
	Actions   []string `json:"actions"`
	Targets   []string `json:"targets"`
	Scopes    []string `json:"scopes"`
	Effect    string   `json:"effect"`
}

// Request is the MASG v1.0.0 authorization decision envelope.
type Request struct {
	ProtocolVersion string `json:"protocol_version"`
	MessageType     string `json:"message_type"`
	RequestID       string `json:"request_id"`
	IssuedAt        string `json:"issued_at"`
	ExpiresAt       string `json:"expires_at"`
	Principal       string `json:"principal"`
	Action          string `json:"action"`
	Target          string `json:"target"`
	Scope           string `json:"scope"`
	PolicyVersion   string `json:"policy_version"`
	ProvenanceRef   string `json:"provenance_ref,omitempty"`
}

// Result is the deterministic policy outcome for one request.
type Result struct {
	Decision      string `json:"decision"`
	ReasonCode    string `json:"reason_code"`
	PolicyVersion string `json:"policy_version"`
}

func result(decision, reason, version string) Result {
	return Result{Decision: decision, ReasonCode: reason, PolicyVersion: version}
}

func validText(value string, max int) bool {
	return utf8.ValidString(value) && strings.TrimSpace(value) != "" && utf8.RuneCountInString(value) <= max
}

func validSelectorList(values []string, maxLength int) bool {
	if len(values) == 0 || len(values) > maxSelectors {
		return false
	}
	seen := make(map[string]struct{}, len(values))
	for _, value := range values {
		if !validText(value, maxLength) {
			return false
		}
		if _, exists := seen[value]; exists {
			return false
		}
		seen[value] = struct{}{}
	}
	return true
}

func validatePolicy(policy Policy) error {
	if !validText(policy.Version, 128) {
		return errors.New("policy version invalid")
	}
	if policy.DefaultEffect != "DENY" {
		return errors.New("policy must default to DENY")
	}
	if policy.Rules == nil {
		return errors.New("policy rules must be an array")
	}
	if len(policy.Rules) > maxRules {
		return errors.New("too many policy rules")
	}
	for _, rule := range policy.Rules {
		if !validText(rule.ID, 128) ||
			!validSelectorList(rule.Principals, 1024) ||
			!validSelectorList(rule.Actions, 256) ||
			!validSelectorList(rule.Targets, 512) ||
			!validSelectorList(rule.Scopes, 512) {
			return errors.New("policy rule or selector invalid")
		}
		switch rule.Effect {
		case "ALLOW", "DENY", "REVIEW_REQUIRED":
		default:
			return errors.New("unsupported policy effect")
		}
	}
	return nil
}

func validateRequest(request Request, policy Policy, now time.Time) (time.Time, time.Time, string) {
	if request.ProtocolVersion != ProtocolVersion || request.MessageType != "authorization_request" {
		return time.Time{}, time.Time{}, "REQUEST_INVALID"
	}
	if !uuidV4Pattern.MatchString(request.RequestID) {
		return time.Time{}, time.Time{}, "REQUEST_INVALID"
	}
	if !validText(request.Principal, 1024) ||
		!validText(request.Action, 256) ||
		!validText(request.Target, 512) ||
		!validText(request.Scope, 512) ||
		!validText(request.PolicyVersion, 128) ||
		(request.ProvenanceRef != "" && (!utf8.ValidString(request.ProvenanceRef) || utf8.RuneCountInString(request.ProvenanceRef) > 2048)) {
		return time.Time{}, time.Time{}, "REQUEST_INVALID"
	}
	if request.PolicyVersion != policy.Version {
		return time.Time{}, time.Time{}, "POLICY_VERSION_MISMATCH"
	}
	if !rfc3339Pattern.MatchString(request.IssuedAt) || strings.HasSuffix(request.IssuedAt, "-00:00") {
		return time.Time{}, time.Time{}, "REQUEST_INVALID"
	}
	issued, err := time.Parse(time.RFC3339Nano, request.IssuedAt)
	if err != nil {
		return time.Time{}, time.Time{}, "REQUEST_INVALID"
	}
	if !rfc3339Pattern.MatchString(request.ExpiresAt) || strings.HasSuffix(request.ExpiresAt, "-00:00") {
		return time.Time{}, time.Time{}, "REQUEST_INVALID"
	}
	expires, err := time.Parse(time.RFC3339Nano, request.ExpiresAt)
	if err != nil {
		return time.Time{}, time.Time{}, "REQUEST_INVALID"
	}
	if !expires.After(issued) {
		return time.Time{}, time.Time{}, "INVALID_VALIDITY_WINDOW"
	}
	if now.IsZero() {
		return time.Time{}, time.Time{}, "CLOCK_INVALID"
	}
	if now.Before(issued) {
		return time.Time{}, time.Time{}, "NOT_YET_VALID"
	}
	if !now.Before(expires) {
		return time.Time{}, time.Time{}, "EXPIRED"
	}
	return issued, expires, ""
}

// Evaluate returns a deny-by-default result using exact selector matching.
// The caller must supply a principal derived from a trusted identity adapter.
// This function does not authenticate that principal or mediate side effects.
func Evaluate(policy Policy, request Request, now time.Time) Result {
	version := policy.Version
	if err := validatePolicy(policy); err != nil {
		return result("DENY", "POLICY_INVALID", version)
	}
	if _, _, reason := validateRequest(request, policy, now); reason != "" {
		return result("DENY", reason, version)
	}

	allow, review := false, false
	for _, rule := range policy.Rules {
		if contains(rule.Principals, request.Principal) &&
			contains(rule.Actions, request.Action) &&
			contains(rule.Targets, request.Target) &&
			contains(rule.Scopes, request.Scope) {
			switch rule.Effect {
			case "DENY":
				return result("DENY", "EXPLICIT_DENY", version)
			case "REVIEW_REQUIRED":
				review = true
			case "ALLOW":
				allow = true
			}
		}
	}
	if review {
		return result("REVIEW_REQUIRED", "APPROVAL_REQUIRED", version)
	}
	if allow {
		return result("ALLOW", "EXPLICIT_MATCH", version)
	}
	return result("DENY", "NO_MATCH", version)
}

func contains(values []string, wanted string) bool {
	for _, value := range values {
		if value == wanted {
			return true
		}
	}
	return false
}

// EvaluateJSON strictly parses both documents before evaluating them.
// Duplicate keys, unknown fields, non-standard JSON, excessive nesting and oversized
// documents fail closed. It does not provide authenticated identity or replay storage.
func EvaluateJSON(policyJSON, requestJSON []byte, now time.Time) Result {
	var policy Policy
	if err := decodeUniqueJSON(policyJSON, &policy, maxPolicyJSONBytes); err != nil {
		return result("DENY", "POLICY_INVALID", "UNKNOWN")
	}
	if err := validatePolicy(policy); err != nil {
		return result("DENY", "POLICY_INVALID", policy.Version)
	}
	var request Request
	if err := decodeUniqueJSON(requestJSON, &request, maxRequestJSONBytes); err != nil {
		return result("DENY", "REQUEST_INVALID", policy.Version)
	}
	return Evaluate(policy, request, now)
}

func decodeUniqueJSON(raw []byte, target any, maxBytes int) error {
	if !utf8.Valid(raw) {
		return errors.New("invalid UTF-8")
	}
	if len(raw) == 0 || len(raw) > maxBytes {
		return errors.New("JSON size invalid")
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	value, err := parseValue(decoder, 1)
	if err != nil {
		return err
	}
	if _, err := decoder.Token(); err != io.EOF {
		if err == nil {
			return errors.New("trailing JSON value")
		}
		return err
	}
	normalized, err := json.Marshal(value)
	if err != nil {
		return err
	}
	strict := json.NewDecoder(bytes.NewReader(normalized))
	strict.DisallowUnknownFields()
	if err := strict.Decode(target); err != nil {
		return err
	}
	return nil
}

func parseValue(decoder *json.Decoder, depth int) (any, error) {
	token, err := decoder.Token()
	if err != nil {
		return nil, err
	}
	delimiter, isDelimiter := token.(json.Delim)
	if !isDelimiter {
		return token, nil
	}
	if depth > maxJSONDepth {
		return nil, errors.New("JSON nesting too deep")
	}
	switch delimiter {
	case '{':
		object := make(map[string]any)
		for decoder.More() {
			keyToken, err := decoder.Token()
			if err != nil {
				return nil, err
			}
			key, ok := keyToken.(string)
			if !ok {
				return nil, errors.New("object key is not a string")
			}
			if _, exists := object[key]; exists {
				return nil, fmt.Errorf("duplicate object key %q", key)
			}
			value, err := parseValue(decoder, depth+1)
			if err != nil {
				return nil, err
			}
			object[key] = value
		}
		end, err := decoder.Token()
		if err != nil || end != json.Delim('}') {
			return nil, errors.New("object terminator invalid")
		}
		return object, nil
	case '[':
		array := make([]any, 0)
		for decoder.More() {
			value, err := parseValue(decoder, depth+1)
			if err != nil {
				return nil, err
			}
			array = append(array, value)
		}
		end, err := decoder.Token()
		if err != nil || end != json.Delim(']') {
			return nil, errors.New("array terminator invalid")
		}
		return array, nil
	default:
		return nil, errors.New("unexpected JSON delimiter")
	}
}
