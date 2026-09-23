from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


class PolicyEngine:
    """Allowlist determinista con default-deny."""

    def __init__(self, allowed_nodes: set[str] | None = None):
        self.allowed_nodes = set(allowed_nodes or ())

    def authorize(self, node_id: str) -> PolicyDecision:
        if node_id in self.allowed_nodes:
            return PolicyDecision(True, "allowlist")
        return PolicyDecision(False, "default_deny")
