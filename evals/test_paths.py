from pathlib import Path

import pytest

from harness.paths import PathResolver, Violation


CASES = [
    ("project:WORK/borrador.md", True, "ok"),
    ("project:INPUT/raw/fuente.pdf", False, "ok"),
    ("project:INPUT/raw/fuente.pdf", True, "entrada_sellada"),
    ("project:../otro/OUTPUT/v1/x.md", False, "intento_de_escape"),
    ("factory:manifests/policy.json", True, "fabrica_es_solo_lectura"),
    ("project:OUTPUT/v0.1/informe.md", True, "salida_write_once"),
]


@pytest.fixture
def resolver(tmp_path: Path) -> PathResolver:
    project = tmp_path / "project"
    factory = tmp_path / "factory"
    (project / "WORK").mkdir(parents=True)
    (project / "INPUT" / "raw").mkdir(parents=True)
    (project / "OUTPUT" / "v0.1").mkdir(parents=True)
    (factory / "manifests").mkdir(parents=True)
    (project / "INPUT" / "raw" / "fuente.pdf").write_text("input", encoding="utf-8")
    (project / "OUTPUT" / "v0.1" / "informe.md").write_text("existing", encoding="utf-8")
    return PathResolver(project, factory)


@pytest.mark.parametrize("logical,write,expected", CASES)
def test_bateria_oficial_de_rutas(resolver: PathResolver, logical: str, write: bool, expected: str):
    result = resolver.resolve(logical, write=write)
    if expected == "ok":
        assert isinstance(result, Path)
        assert result.is_absolute()
    else:
        assert isinstance(result, Violation)
        assert result.code == expected
