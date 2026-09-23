from __future__ import annotations

from pathlib import Path
from typing import Callable

from .budget import BudgetManager
from .policy import PolicyEngine
from .taint import TaintFilter
from .trace import TraceWriter
from .types import (
    Checkpoint,
    NodeSpec,
    RunResult,
    ToolResult,
    BudgetState,
    TERMINAL_ABORTADO,
    TERMINAL_AGOTADO,
    TERMINAL_COMPLETADO,
)

_GATE_TOKEN = object()


def execute_node(executor: Callable[[], ToolResult], trace: TraceWriter, *, gate_token=None) -> ToolResult:
    """Punto de ejecución interno. Sin token de la puerta, deniega y registra."""
    if gate_token is not _GATE_TOKEN:
        trace.record(
            "direct_execution_denied",
            verdict="denied",
            reason="outside_unique_gate",
        )
        return ToolResult(
            ok=False,
            error_code="outside_unique_gate",
            message="La ejecución directa está denegada; use Harness.run.",
            recoverable=False,
        )
    return executor()


class Harness:
    """Puerta única mínima y determinista para la fábrica T1."""

    def __init__(self, *, allowed_nodes: set[str], trace_dir: Path):
        self.policy = PolicyEngine(allowed_nodes)
        self.trace_dir = trace_dir

    @staticmethod
    def _checkpoint(run_id: str, terminal: str, budget: BudgetState) -> Checkpoint:
        return Checkpoint(
            run_id=run_id,
            terminal=terminal,
            budget_after=budget.snapshot(),
            effects_applied=(),
            resume_from="PREPARANDO",
        )

    def run(self, node: NodeSpec, budget: BudgetState, *, run_id: str) -> RunResult:
        trace = TraceWriter(self.trace_dir / f"{run_id}.jsonl", run_id)
        terminal = TERMINAL_ABORTADO
        quarantined: list[dict[str, str]] = []
        try:
            trace.record("run_started", phase="PREPARANDO", node=node.id)

            policy = self.policy.authorize(node.id)
            trace.record("policy_checked", node=node.id, allowed=policy.allowed, reason=policy.reason)
            if not policy.allowed:
                terminal = TERMINAL_ABORTADO
                return RunResult(
                    status=terminal,
                    error={"error_code": "policy_denied", "reason": policy.reason},
                    checkpoint=self._checkpoint(run_id, terminal, budget),
                )

            reservation = BudgetManager.reserve(node.estimate, budget)
            trace.record(
                "budget_checked",
                before=reservation.before,
                after=reservation.after,
                allowed=reservation.ok,
                deficits=list(reservation.deficits),
            )
            if not reservation.ok:
                terminal = TERMINAL_AGOTADO
                trace.record(
                    "partial_checkpoint",
                    terminal=terminal,
                    incomplete=True,
                    resumable=True,
                    effects_applied=[],
                    idempotency_keys=[],
                )
                return RunResult(
                    status=terminal,
                    payload={"incomplete": True, "resumable": True},
                    error={"error_code": "budget_exhausted", "deficits": list(reservation.deficits)},
                    checkpoint=self._checkpoint(run_id, terminal, budget),
                )

            included_locators: list[str] = []
            for fragment in node.fragments:
                verdict = TaintFilter.review(fragment)
                if verdict.taint == "tainted":
                    entry = {
                        "source": verdict.source,
                        "locator": verdict.locator,
                        "action": verdict.action,
                    }
                    quarantined.append(entry)
                    trace.record("fragment_quarantined", **entry, run_continues=True)
                else:
                    included_locators.append(fragment.localizador)
            trace.record("context_built", included_locators=included_locators)

            result = execute_node(node.execute, trace, gate_token=_GATE_TOKEN)
            if not result.ok:
                trace.record(
                    "tool_error",
                    error_code=result.error_code,
                    message=result.message,
                    recoverable=result.recoverable,
                    suggestion=result.suggestion,
                )
                if result.recoverable and node.recovery is not None:
                    trace.record("recovery_route", action="retry_with_declared_recovery")
                    result = node.recovery(result)

            if not result.ok:
                terminal = TERMINAL_ABORTADO
                return RunResult(
                    status=terminal,
                    error={
                        "error_code": result.error_code,
                        "message": result.message,
                        "recoverable": result.recoverable,
                        "suggestion": result.suggestion,
                    },
                    checkpoint=self._checkpoint(run_id, terminal, budget),
                    quarantined=tuple(quarantined),
                )

            trace.record("output_validated", ok=True)
            terminal = TERMINAL_COMPLETADO
            return RunResult(
                status=terminal,
                payload=result.value,
                checkpoint=self._checkpoint(run_id, terminal, budget),
                quarantined=tuple(quarantined),
            )
        except Exception as exc:
            terminal = TERMINAL_ABORTADO
            trace.record(
                "unhandled_error_as_data",
                error_code=type(exc).__name__,
                message=str(exc),
            )
            return RunResult(
                status=terminal,
                error={"error_code": type(exc).__name__, "message": str(exc)},
                checkpoint=self._checkpoint(run_id, terminal, budget),
                quarantined=tuple(quarantined),
            )
        finally:
            trace.record("run_finished", terminal=terminal)
            trace.close()
