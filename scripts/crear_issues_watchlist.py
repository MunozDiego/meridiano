#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crea/actualiza issues de GitHub para los cruces vigentes de la watchlist
-- ultimo paso del monitor en `diario.yml`, tras `monitor_watchlist.py`.

Usa el `gh` CLI (preinstalado en los runners de GitHub Actions) autenticado
con el `GITHUB_TOKEN` nativo del Action (via `GH_TOKEN` en el entorno) --
sin secrets nuevos. Corre desde la raiz del repo `publico/` checked-out por
el Action, donde `gh` detecta el repo del remoto `origin` automaticamente.

Deduplicacion: maximo 1 issue abierto por ticker. Si ya existe uno abierto
para el ticker en alerta, se le agrega un comentario con el estado del dia
(asi "los dias consecutivos se acumulan en el mismo" issue, sin spam de
issues nuevos); si no existe, se crea.

No requiere red mas alla de la API de GitHub (via `gh`) -- no se corre en
el test local de MER-F2I (ver Log de esa fase), solo en el Action real.

Uso: python3 scripts/crear_issues_watchlist.py
"""
import json
import subprocess
import sys
from pathlib import Path

PUBLICO_DIR = Path(__file__).resolve().parents[1]
ALERTAS_JSON = PUBLICO_DIR / "data" / "alertas.json"

EMPRESA_URL_BASE = "https://d24hipm8fjmcql.cloudfront.net/empresa"

DISCLAIMER = (
    "_Esta alerta informa que se alcanzo la condicion de precio del reporte. "
    "No es una recomendacion de compra automatica: la decision sigue exigiendo "
    "registro humano en el DecisionLog (`insertar_decision()`)._"
)


def _gh(*args):
    return subprocess.run(["gh", *args], cwd=PUBLICO_DIR, capture_output=True, text=True)


def _titulo(ticker, cierre, precio_maximo):
    return f"WATCHLIST: {ticker} cruzó su precio máximo ({cierre:.2f} ≤ {precio_maximo:.2f})"


def _cuerpo(alerta):
    return (
        f"**Ticker:** {alerta['ticker']}\n"
        f"**Cierre:** {alerta['cierre']:.2f}\n"
        f"**Precio máximo de compra:** {alerta['precio_maximo']:.2f}\n"
        f"**Fecha:** {alerta['fecha']}\n"
        f"**Días consecutivos bajo el máximo:** {alerta['dias_consecutivos']}\n\n"
        f"Página de la empresa: {EMPRESA_URL_BASE}/{alerta['ticker']}\n\n"
        f"{DISCLAIMER}"
    )


def _issue_abierto(ticker):
    r = _gh("issue", "list", "--state", "open", "--json", "number,title", "--limit", "200")
    if r.returncode != 0:
        print(f"ERROR: gh issue list fallo: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    prefijo = f"WATCHLIST: {ticker} cruzó"
    for it in json.loads(r.stdout or "[]"):
        if it["title"].startswith(prefijo):
            return it["number"]
    return None


def main():
    if not ALERTAS_JSON.exists():
        print("crear_issues_watchlist: no existe alertas.json -- nada que hacer.")
        sys.exit(0)

    alertas = json.loads(ALERTAS_JSON.read_text(encoding="utf-8")).get("alertas", [])
    if not alertas:
        print("crear_issues_watchlist: sin cruces vigentes -- nada que hacer.")
        sys.exit(0)

    for alerta in alertas:
        ticker = alerta["ticker"]
        numero = _issue_abierto(ticker)
        cuerpo = _cuerpo(alerta)

        if numero is None:
            titulo = _titulo(ticker, alerta["cierre"], alerta["precio_maximo"])
            r = _gh("issue", "create", "--title", titulo, "--body", cuerpo)
            if r.returncode != 0:
                print(f"ERROR: gh issue create fallo para {ticker}: {r.stderr}", file=sys.stderr)
                sys.exit(1)
            print(f"issue creado para {ticker}: {r.stdout.strip()}")
        else:
            r = _gh("issue", "comment", str(numero), "--body", cuerpo)
            if r.returncode != 0:
                print(f"ERROR: gh issue comment fallo para {ticker} #{numero}: {r.stderr}", file=sys.stderr)
                sys.exit(1)
            print(f"issue #{numero} actualizado para {ticker} (dia {alerta['dias_consecutivos']}).")

    print("crear_issues_watchlist OK.")


if __name__ == "__main__":
    main()
