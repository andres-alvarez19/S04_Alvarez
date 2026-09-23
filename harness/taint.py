from __future__ import annotations

import re
from dataclasses import dataclass

from .types import Fragment


MARKERS = (
    r"ignora (tus|las) (reglas|instrucciones)",
    r"eres ahora",
    r"system prompt",
    r"revela (tu|el) prompt",
    r"env[ií]a .* a https?://",
    r"<\|im_start\|>",
    r"presupuesto .* ampliado",
)


@dataclass(frozen=True)
class TaintVerdict:
    taint: str
    action: str
    source: str
    locator: str


class TaintFilter:
    """Detector de aviso: la defensa real es que el fragmento no obtiene autoridad."""

    @staticmethod
    def review(fragment: Fragment) -> TaintVerdict:
        poisoned = any(re.search(pattern, fragment.texto, re.I) for pattern in MARKERS)
        if poisoned:
            return TaintVerdict("tainted", "cuarentena", fragment.fuente, fragment.localizador)
        return TaintVerdict("clean", "incluir", fragment.fuente, fragment.localizador)
