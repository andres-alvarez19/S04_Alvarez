from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Violation:
    code: str
    logical_path: str
    invariant: str | None = None


class PathResolver:
    """Único resolutor de rutas lógicas de la fábrica.

    Las violaciones vuelven como datos. La comparación de contención se hace
    sobre rutas resueltas, nunca con prefijos de texto.
    """

    _SOLO_LECTURA = {"INPUT"}

    def __init__(self, project_root: Path, factory_root: Path, *, mode: str = "project_run"):
        self.project_root = project_root.resolve()
        self.factory_root = factory_root.resolve()
        self.mode = mode

    @staticmethod
    def _inside(base: Path, destination: Path) -> bool:
        try:
            destination.relative_to(base)
            return True
        except ValueError:
            return False

    def resolve(self, logical: str, *, write: bool):
        root, sep, rel = logical.partition(":")
        if not sep or not rel:
            return Violation("ruta_logica_invalida", logical)

        base = {"project": self.project_root, "factory": self.factory_root}.get(root)
        if base is None:
            return Violation("raiz_desconocida", logical)

        destination = (base / rel).resolve()
        if not self._inside(base, destination):
            return Violation("intento_de_escape", logical, "I1/I3")

        if not write:
            return destination

        if root == "factory" and self.mode != "factory_improvement":
            return Violation("fabrica_es_solo_lectura", logical, "I2")

        first_segment = Path(rel).parts[0] if Path(rel).parts else ""
        if root == "project" and first_segment in self._SOLO_LECTURA:
            return Violation("entrada_sellada", logical, "I4")

        if root == "project" and first_segment == "OUTPUT" and destination.exists():
            return Violation("salida_write_once", logical, "I5")

        return destination
