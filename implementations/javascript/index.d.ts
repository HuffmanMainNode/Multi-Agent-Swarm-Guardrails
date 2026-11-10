export type Decision = "ALLOW" | "DENY" | "REVIEW_REQUIRED";
export interface DecisionResult {
  decision: Decision;
  reason_code: string;
  policy_version: string;
}
export interface PolicyRule {
  id: string;
  principals: string[];
  actions: string[];
  targets: string[];
  scopes: string[];
  effect: "ALLOW" | "DENY" | "REVIEW_REQUIRED";
}
export interface Policy {
  version: string;
  default_effect: "DENY";
  rules: PolicyRule[];
}
export interface AuthorizationRequest {
  protocol_version: "1.0.0";
  message_type: "authorization_request";
  request_id: string;
  issued_at: string;
  expires_at: string;
  principal: string;
  action: string;
  target: string;
  scope: string;
  policy_version: string;
  provenance_ref?: string;
}
export declare const PROTOCOL_VERSION: "1.0.0";
export declare function evaluate(policy: Policy, request: AuthorizationRequest, now?: Date): DecisionResult;
export declare function evaluateJSON(policyInput: string | Uint8Array, requestInput: string | Uint8Array, now?: Date): DecisionResult;
export declare const limits: Readonly<{
  maxPolicyBytes: number;
  maxRequestBytes: number;
  maxJsonDepth: number;
  maxRules: number;
  maxSelectors: number;
}>;
