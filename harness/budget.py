from __future__ import annotations

from dataclasses import dataclass

from .types import BudgetEstimate, BudgetState


@dataclass(frozen=True)
class BudgetDecision:
    ok: bool
    before: dict[str, int | float]
    after: dict[str, int | float]
    deficits: tuple[str, ...] = ()


class BudgetManager:
    """Comprueba y reserva los cuatro presupuestos antes de ejecutar."""

    @staticmethod
    def reserve(estimate: BudgetEstimate, state: BudgetState) -> BudgetDecision:
        before = state.snapshot()
        deficits: list[str] = []

        if estimate.steps > state.steps_remaining:
            deficits.append("steps")
        if estimate.tokens > state.tokens_remaining:
            deficits.append("tokens")
        if estimate.seconds > state.seconds_remaining:
            deficits.append("time")
        if estimate.cost_usd > state.cost_usd_remaining + 1e-12:
            deficits.append("money")

        if deficits:
            return BudgetDecision(False, before, before, tuple(deficits))

        state.steps_remaining -= estimate.steps
        state.tokens_remaining -= estimate.tokens
        state.seconds_remaining = round(state.seconds_remaining - estimate.seconds, 6)
        state.cost_usd_remaining = round(state.cost_usd_remaining - estimate.cost_usd, 6)
        return BudgetDecision(True, before, state.snapshot())
