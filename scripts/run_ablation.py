#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_pytest(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=no"],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    print("=== ABLACIÓN: retirar control I5 salida write-once del PathResolver ===")
    with tempfile.TemporaryDirectory(prefix="s04-ablation-") as tmp:
        target = Path(tmp) / "repo"
        shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        paths_file = target / "harness" / "paths.py"
        source = paths_file.read_text(encoding="utf-8")
        needle = 'if root == "project" and first_segment == "OUTPUT" and destination.exists():'
        if needle not in source:
            raise SystemExit("No se encontró el control I5 esperado para la ablación.")
        paths_file.write_text(source.replace(needle, 'if False and root == "project" and first_segment == "OUTPUT" and destination.exists():'), encoding="utf-8")
        ablated = run_pytest(target)
        print(ablated.stdout.rstrip())
        if ablated.stderr.strip():
            print(ablated.stderr.rstrip())
        if ablated.returncode == 0:
            raise SystemExit("La ablación no produjo fallo: evidencia inválida.")

    print("\n=== RESTAURACIÓN: control I5 presente ===")
    restored = run_pytest(ROOT)
    print(restored.stdout.rstrip())
    if restored.stderr.strip():
        print(restored.stderr.rstrip())
    if restored.returncode != 0:
        raise SystemExit("La batería restaurada no volvió a verde.")

    print("\nABLATION_EVIDENCE_OK removed=I5 failure_class=overwrite_existing_output production=version_overwrite_without_write_once")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
