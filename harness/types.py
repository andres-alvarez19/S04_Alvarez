from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


TERMINAL_COMPLETADO = "COMPLETADO"
TERMINAL_AGOTADO = "AGOTADO"
TERMINAL_ABORTADO = "ABORTADO"


@dataclass(frozen=True)
class Fragment:
    fuente: str
    localizador: str
    texto: str


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    value: Any = None
    error_code: str | None = None
    message: str | None = None
    recoverable: bool = False
    suggestion: str | None = None


@dataclass(frozen=True)
class BudgetEstimate:
    steps: int = 1
    tokens: int = 0
    seconds: float = 0.0
    cost_usd: float = 0.0


@dataclass
class BudgetState:
    steps_remaining: int
    tokens_remaining: int
    seconds_remaining: float
    cost_usd_remaining: float

    def snapshot(self) -> dict[str, int | float]:
        return {
            "steps_remaining": self.steps_remaining,
            "tokens_remaining": self.tokens_remaining,
            "seconds_remaining": round(self.seconds_remaining, 6),
            "cost_usd_remaining": round(self.cost_usd_remaining, 6),
        }


@dataclass(frozen=True)
class NodeSpec:
    id: str
    estimate: BudgetEstimate
    execute: Callable[[], ToolResult]
    recovery: Callable[[ToolResult], ToolResult] | None = None
    fragments: tuple[Fragment, ...] = ()


@dataclass(frozen=True)
class Checkpoint:
    run_id: str
    terminal: str
    budget_after: dict[str, int | float]
    effects_applied: tuple[dict[str, str], ...] = ()
    resume_from: str = "PREPARANDO"


@dataclass(frozen=True)
class RunResult:
    status: str
    payload: Any = None
    error: dict[str, Any] | None = None
    checkpoint: Checkpoint | None = None
    quarantined: tuple[dict[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "payload": self.payload,
            "error": self.error,
            "checkpoint": None
            if self.checkpoint is None
            else {
                "run_id": self.checkpoint.run_id,
                "terminal": self.checkpoint.terminal,
                "budget_after": self.checkpoint.budget_after,
                "effects_applied": list(self.checkpoint.effects_applied),
                "resume_from": self.checkpoint.resume_from,
            },
            "quarantined": list(self.quarantined),
        }
