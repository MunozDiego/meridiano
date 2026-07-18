#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Captura diaria del repo publico de Meridiano -- corre en el GitHub Action
(`diario.yml`), sin acceso a la DB privada ni a `datos/` de `~/Code/Meridiano`.
Todo lo que necesita vive dentro de `publico/`.

Pasos:
1. Captura el nivel IPSA vivo (mismo metodo que `datos/scripts/04_benchmark.py`
   de Fase 1A: `^IPSA` en Yahoo, `period='5d'`, ultimo Close no-cero) -> apendea
   a `data/ipsa_nivel_diario.csv` (idempotente por fecha).
2. Captura los cierres de los tickers en `data/holdings_snapshot.json` (si hay
   posiciones) -> apendea a `data/precios_holdings.csv` (idempotente por
   fecha+ticker).
3. Captura la UF del dia (mindicador.cl, mismo mirror que
   `datos/scripts/03_macro.py`) -> apendea a `data/uf_diaria.csv` (idempotente
   por fecha).
4. Recalcula la serie de NAV dual CLP/UF (version standalone, portada de
   `app/backend/performance.py`, que aca lee holdings desde
   `holdings_snapshot.json` en vez de la DB) -> apendea una fila a
   `data/nav_serie.csv` (idempotente por fecha; si la fecha de hoy ya tiene
   fila, no duplica) y regenera `sitio/data/nav.json` completo desde ese csv.

Idempotente de punta a punta: correr dos veces el mismo dia deja el working
tree limpio la segunda vez (ninguna fila se duplica, ningun JSON cambia si
los insumos no cambiaron).

Uso: python3 scripts/captura_diaria.py
"""
import csv
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests
import yfinance as yf

PUBLICO_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PUBLICO_DIR / "data"
SITIO_DATA_DIR = PUBLICO_DIR / "sitio" / "data"

HOLDINGS_SNAPSHOT = DATA_DIR / "holdings_snapshot.json"
IPSA_CSV = DATA_DIR / "ipsa_nivel_diario.csv"
UF_CSV = DATA_DIR / "uf_diaria.csv"
PRECIOS_HOLDINGS_CSV = DATA_DIR / "precios_holdings.csv"
NAV_SERIE_CSV = DATA_DIR / "nav_serie.csv"
NAV_JSON = SITIO_DATA_DIR / "nav.json"

BENCHMARK_YAHOO = "^IPSA"
BENCHMARK_LABEL_DEFAULT = "Benchmark: IPSA (nivel vivo capturado dia a dia desde el repo publico)."


# ---------------------------------------------------------------------------
# Captura
# ---------------------------------------------------------------------------

def _leer_csv(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _escribir_csv(path, filas, columnas):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columnas)
        w.writeheader()
        for f in filas:
            w.writerow(f)


def capturar_ipsa_vivo():
    filas = _leer_csv(IPSA_CSV)
    fechas_existentes = {f["fecha"] for f in filas}

    h = yf.Ticker(BENCHMARK_YAHOO).history(period="5d", interval="1d", auto_adjust=False, timeout=10)
    if h is None or h.empty:
        print("ERROR: ^IPSA no devolvio datos en period='5d'.", file=sys.stderr)
        sys.exit(1)
    h.index = h.index.tz_localize(None) if h.index.tz is not None else h.index
    no_cero = h[h["Close"] > 0]
    if no_cero.empty:
        print("ERROR: todas las filas de ^IPSA period='5d' tienen Close<=0.", file=sys.stderr)
        sys.exit(1)

    ultima = no_cero.iloc[-1]
    fecha_nivel = str(no_cero.index[-1].date())
    if fecha_nivel in fechas_existentes:
        print(f"IPSA: {fecha_nivel} ya existe -- no se duplica.")
        return

    filas.append({
        "fecha": fecha_nivel,
        "close_ipsa": f"{float(ultima['Close']):.4f}",
        "fecha_descarga": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    })
    filas.sort(key=lambda f: f["fecha"])
    _escribir_csv(IPSA_CSV, filas, ["fecha", "close_ipsa", "fecha_descarga"])
    print(f"IPSA: apendeado {fecha_nivel} = {float(ultima['Close']):.2f}.")


def capturar_precios_holdings(tickers):
    if not tickers:
        print("Holdings: portafolio 100% caja, sin tickers que capturar.")
        return

    filas = _leer_csv(PRECIOS_HOLDINGS_CSV)
    existentes = {(f["fecha"], f["ticker"]) for f in filas}

    for ticker in tickers:
        h = yf.Ticker(ticker).history(period="5d", interval="1d", auto_adjust=False, timeout=10)
        if h is None or h.empty:
            print(f"ERROR: {ticker} no devolvio datos en period='5d'.", file=sys.stderr)
            sys.exit(1)
        h.index = h.index.tz_localize(None) if h.index.tz is not None else h.index
        no_cero = h[h["Close"] > 0]
        if no_cero.empty:
            print(f"ERROR: todas las filas de {ticker} period='5d' tienen Close<=0.", file=sys.stderr)
            sys.exit(1)
        ultima = no_cero.iloc[-1]
        fecha_cierre = str(no_cero.index[-1].date())
        if (fecha_cierre, ticker) in existentes:
            print(f"Holdings: {ticker} {fecha_cierre} ya existe -- no se duplica.")
            continue
        filas.append({
            "fecha": fecha_cierre,
            "ticker": ticker,
            "close": f"{float(ultima['Close']):.4f}",
            "fecha_descarga": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        })
        existentes.add((fecha_cierre, ticker))
        print(f"Holdings: apendeado {ticker} {fecha_cierre} = {float(ultima['Close']):.2f}.")

    filas.sort(key=lambda f: (f["fecha"], f["ticker"]))
    _escribir_csv(PRECIOS_HOLDINGS_CSV, filas, ["fecha", "ticker", "close", "fecha_descarga"])


def capturar_uf_hoy():
    filas = _leer_csv(UF_CSV)
    fechas_existentes = {f["fecha"] for f in filas}

    r = requests.get("https://mindicador.cl/api/uf", timeout=20)
    r.raise_for_status()
    serie = r.json().get("serie", [])
    if not serie:
        print("ERROR: mindicador.cl/api/uf no devolvio serie.", file=sys.stderr)
        sys.exit(1)
    ultimo = serie[0]  # mindicador.cl devuelve la serie ordenada mas reciente primero
    fecha_uf = ultimo["fecha"][:10]
    if fecha_uf in fechas_existentes:
        print(f"UF: {fecha_uf} ya existe -- no se duplica.")
        return

    filas.append({"fecha": fecha_uf, "uf": f"{float(ultimo['valor']):.4f}"})
    filas.sort(key=lambda f: f["fecha"])
    _escribir_csv(UF_CSV, filas, ["fecha", "uf"])
    print(f"UF: apendeado {fecha_uf} = {float(ultimo['valor']):.2f}.")


def _asegurar_uf_historica(fecha_iso):
    """Garantiza que `uf_diaria.csv` tenga una fila para `fecha_iso` (necesaria
    para indexar la serie de NAV en UF desde `fecha_inicio` del portafolio,
    que puede ser anterior al primer `capturar_uf_hoy()`). Si falta, la pide
    a mindicador.cl por fecha especifica en vez de "la de hoy".
    """
    filas = _leer_csv(UF_CSV)
    if any(f["fecha"] == fecha_iso for f in filas):
        return
    dd, mm, yyyy = fecha_iso[8:10], fecha_iso[5:7], fecha_iso[0:4]
    r = requests.get(f"https://mindicador.cl/api/uf/{dd}-{mm}-{yyyy}", timeout=20)
    r.raise_for_status()
    serie = r.json().get("serie", [])
    if not serie:
        print(f"ERROR: mindicador.cl no tiene UF para {fecha_iso}.", file=sys.stderr)
        sys.exit(1)
    valor = float(serie[0]["valor"])
    filas.append({"fecha": fecha_iso, "uf": f"{valor:.4f}"})
    filas.sort(key=lambda f: f["fecha"])
    _escribir_csv(UF_CSV, filas, ["fecha", "uf"])
    print(f"UF: apendeada fecha historica {fecha_iso} = {valor:.2f} (base de la serie).")


# ---------------------------------------------------------------------------
# NAV standalone (portado de app/backend/performance.py, sin DB)
# ---------------------------------------------------------------------------

def _ultimo_valor_a_fecha(filas, fecha, col_fecha, col_valor, filtro=None):
    candidatas = [
        f for f in filas
        if f[col_fecha] <= fecha and (filtro is None or filtro(f))
    ]
    if not candidatas:
        return None
    return float(max(candidatas, key=lambda f: f[col_fecha])[col_valor])


def _leer_benchmark_label_actual():
    if NAV_JSON.exists():
        try:
            actual = json.loads(NAV_JSON.read_text(encoding="utf-8"))
            if actual.get("benchmark_label"):
                return actual["benchmark_label"]
        except (json.JSONDecodeError, OSError):
            pass
    return BENCHMARK_LABEL_DEFAULT


def _seed_nav_serie_si_falta(snapshot):
    if NAV_SERIE_CSV.exists():
        return
    fecha_inicio = snapshot["fecha_inicio"]
    capital = snapshot["capital_inicial_clp"]
    _asegurar_uf_historica(fecha_inicio)
    uf_inicio = _ultimo_valor_a_fecha(_leer_csv(UF_CSV), fecha_inicio, "fecha", "uf")
    fila = {
        "fecha": fecha_inicio,
        "nav_clp": f"{capital:.4f}",
        "nav_uf": f"{capital / uf_inicio:.4f}",
        "index100_clp": "100.0",
        "index100_uf": "100.0",
        "benchmark_index100": "100.0",
    }
    _escribir_csv(NAV_SERIE_CSV, [fila], ["fecha", "nav_clp", "nav_uf", "index100_clp", "index100_uf", "benchmark_index100"])
    print(f"nav_serie: seed inicial en {fecha_inicio} (NAV = capital inicial CLP {capital:,.0f}).")


def _calcular_nav_hoy(snapshot, fecha_hoy):
    caja = snapshot["caja_actual_clp"]
    precios = _leer_csv(PRECIOS_HOLDINGS_CSV)
    valor_posiciones = 0.0
    for h in snapshot["holdings"]:
        ticker = h["ticker"]
        close = _ultimo_valor_a_fecha(precios, fecha_hoy, "fecha", "close", filtro=lambda f, t=ticker: f["ticker"] == t)
        if close is None:
            print(f"ERROR: sin cierre capturado para {ticker} al {fecha_hoy}.", file=sys.stderr)
            sys.exit(1)
        valor_posiciones += float(h["cantidad_acciones"]) * close
    return caja + valor_posiciones


def actualizar_nav_serie_y_json(snapshot):
    _seed_nav_serie_si_falta(snapshot)

    filas = _leer_csv(NAV_SERIE_CSV)
    fecha_hoy = str(date.today())
    fechas_existentes = {f["fecha"] for f in filas}

    if fecha_hoy not in fechas_existentes:
        nav_clp_hoy = _calcular_nav_hoy(snapshot, fecha_hoy)
        uf_hoy = _ultimo_valor_a_fecha(_leer_csv(UF_CSV), fecha_hoy, "fecha", "uf")
        ipsa_hoy = _ultimo_valor_a_fecha(_leer_csv(IPSA_CSV), fecha_hoy, "fecha", "close_ipsa")
        ipsa_base = float(min(_leer_csv(IPSA_CSV), key=lambda f: f["fecha"])["close_ipsa"]) if _leer_csv(IPSA_CSV) else None

        base = min(filas, key=lambda f: f["fecha"]) if filas else None
        nav_clp_base = float(base["nav_clp"]) if base else nav_clp_hoy
        nav_uf_base = float(base["nav_uf"]) if base else (nav_clp_hoy / uf_hoy if uf_hoy else nav_clp_hoy)

        nueva = {
            "fecha": fecha_hoy,
            "nav_clp": f"{nav_clp_hoy:.4f}",
            "nav_uf": f"{(nav_clp_hoy / uf_hoy if uf_hoy else 0.0):.4f}",
            "index100_clp": f"{(nav_clp_hoy / nav_clp_base * 100.0 if nav_clp_base else 100.0):.4f}",
            "index100_uf": f"{((nav_clp_hoy / uf_hoy) / nav_uf_base * 100.0 if uf_hoy and nav_uf_base else 100.0):.4f}",
            "benchmark_index100": f"{(ipsa_hoy / ipsa_base * 100.0 if ipsa_hoy and ipsa_base else 100.0):.4f}",
        }
        filas.append(nueva)
        filas.sort(key=lambda f: f["fecha"])
        _escribir_csv(NAV_SERIE_CSV, filas, ["fecha", "nav_clp", "nav_uf", "index100_clp", "index100_uf", "benchmark_index100"])
        print(f"nav_serie: apendeada fila {fecha_hoy} (NAV CLP {nav_clp_hoy:,.0f}).")
    else:
        print(f"nav_serie: {fecha_hoy} ya existe -- no se duplica.")
        filas = _leer_csv(NAV_SERIE_CSV)

    _exportar_nav_json(filas, snapshot)


def _serie_retornos(valores):
    return [valores[i] / valores[i - 1] - 1 for i in range(1, len(valores)) if valores[i - 1]]


def _max_drawdown(valores):
    pico = valores[0]
    peor = 0.0
    for v in valores:
        pico = max(pico, v)
        peor = min(peor, v / pico - 1 if pico else 0.0)
    return peor


def _exportar_nav_json(filas, snapshot):
    nav_clp = [float(f["nav_clp"]) for f in filas]
    nav_uf = [float(f["nav_uf"]) for f in filas]
    fechas = [f["fecha"] for f in filas]

    retorno_acumulado_clp = nav_clp[-1] / nav_clp[0] - 1 if nav_clp[0] else 0.0
    retorno_acumulado_uf = nav_uf[-1] / nav_uf[0] - 1 if nav_uf[0] else 0.0
    dias = (date.fromisoformat(fechas[-1]) - date.fromisoformat(fechas[0])).days
    anios = dias / 365.25
    ret_anualizado_clp = (1 + retorno_acumulado_clp) ** (1 / anios) - 1 if anios > 0 else 0.0
    ret_anualizado_uf = (1 + retorno_acumulado_uf) ** (1 / anios) - 1 if anios > 0 else 0.0

    rets_clp = _serie_retornos(nav_clp)
    if len(rets_clp) >= 2:
        media = sum(rets_clp) / len(rets_clp)
        varianza = sum((r - media) ** 2 for r in rets_clp) / (len(rets_clp) - 1)
        vol_anualizada = (varianza ** 0.5) * (252 ** 0.5)
    else:
        vol_anualizada = 0.0

    resultado = {
        "tiene_transacciones": len(snapshot["holdings"]) > 0,
        "fecha_inicio": fechas[0],
        "fecha_fin": fechas[-1],
        "benchmark_label": _leer_benchmark_label_actual(),
        "cifras": {
            "clp": {
                "nav_actual": nav_clp[-1],
                "retorno_acumulado": retorno_acumulado_clp,
                "retorno_anualizado": ret_anualizado_clp,
                "volatilidad_anualizada": vol_anualizada,
                "max_drawdown": _max_drawdown(nav_clp),
            },
            "uf": {
                "nav_actual": nav_uf[-1],
                "retorno_acumulado": retorno_acumulado_uf,
                "retorno_anualizado": ret_anualizado_uf,
            },
        },
        "serie": {
            "clp": [
                {"fecha": f["fecha"], "nav": float(f["nav_clp"]), "index100": float(f["index100_clp"]),
                 "benchmark_index100": float(f["benchmark_index100"])}
                for f in filas
            ],
            "uf": [
                {"fecha": f["fecha"], "nav": float(f["nav_uf"]), "index100": float(f["index100_uf"]),
                 "benchmark_index100": float(f["benchmark_index100"])}
                for f in filas
            ],
        },
        "anotaciones": [],
    }
    SITIO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    NAV_JSON.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"nav.json regenerado ({len(filas)} filas en la serie).")


def main():
    if not HOLDINGS_SNAPSHOT.exists():
        print(f"ERROR: falta {HOLDINGS_SNAPSHOT} (correr sync_publico.py primero).", file=sys.stderr)
        sys.exit(1)
    snapshot = json.loads(HOLDINGS_SNAPSHOT.read_text(encoding="utf-8"))
    tickers = [h["ticker"] for h in snapshot["holdings"]]

    capturar_ipsa_vivo()
    capturar_precios_holdings(tickers)
    capturar_uf_hoy()
    actualizar_nav_serie_y_json(snapshot)
    print("captura_diaria OK.")


if __name__ == "__main__":
    main()
