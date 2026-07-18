#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard de publicacion: falla si algo sensible esta a punto de terminar en el
repo publico. Se corre a mano antes de cada commit en `publico/`, como
pre-commit hook local, y como primer paso del workflow diario.

Revisa dos universos, ambos relativos a `publico/` (raiz de este repo):
1. El staging de git (si `publico/` ya es un repo git con cambios agregados).
2. Todo el arbol de archivos trackeable (para el caso "primer commit", donde
   todavia no hay historial git que comparar).

Falla (exit 1) si algun path matchea alguno de los patrones prohibidos.
Uso: python3 scripts/guard_no_privado.py
"""
import subprocess
import sys
from pathlib import Path

PUBLICO_DIR = Path(__file__).resolve().parents[1]

PATRONES_PROHIBIDOS = [
    "fase-0",
    "bibliografia",
    ".db",
    ".env",
    "credencial",
    "credentials",
    ".pem",
    "id_rsa",
]


def _matchea_prohibido(ruta_str):
    ruta_lower = ruta_str.lower()
    return any(patron in ruta_lower for patron in PATRONES_PROHIBIDOS)


def _rutas_staged(cwd):
    """Rutas en el index de git (staged), si `cwd` es un repo git. [] si no."""
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=cwd, capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [l for l in out.stdout.splitlines() if l.strip()]


def _rutas_arbol(cwd):
    """Todo archivo bajo `cwd`, salvo `.git/`."""
    rutas = []
    for p in cwd.rglob("*"):
        if p.is_dir():
            continue
        if ".git" in p.relative_to(cwd).parts:
            continue
        rutas.append(str(p.relative_to(cwd)))
    return rutas


def main():
    candidatas = set(_rutas_staged(PUBLICO_DIR)) | set(_rutas_arbol(PUBLICO_DIR))
    ofensoras = sorted(r for r in candidatas if _matchea_prohibido(r))

    if ofensoras:
        print("GUARD FALLO -- rutas prohibidas encontradas en publico/:", file=sys.stderr)
        for r in ofensoras:
            print(f"  - {r}", file=sys.stderr)
        sys.exit(1)

    print(f"guard_no_privado OK -- {len(candidatas)} rutas revisadas, ninguna prohibida.")
    sys.exit(0)


if __name__ == "__main__":
    main()
