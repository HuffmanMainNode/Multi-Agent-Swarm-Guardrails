from dataclasses import dataclass
from enum import Enum

class Decision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    DENY = "DENY"

@dataclass(frozen=True)
class Evaluation:
    decision: Decision
    reason_code: str
    message: str
    policy_version: str

    def to_dict(self) -> dict[str, str]:
        return {"decision": self.decision.value, "reason_code": self.reason_code,
                "message": self.message, "policy_version": self.policy_version}
