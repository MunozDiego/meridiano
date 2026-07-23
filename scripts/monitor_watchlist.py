#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monitor de watchlist del repo publico de Meridiano -- corre en el GitHub
Action (`diario.yml`) despues de `captura_diaria.py`, sin acceso a la DB
privada. Cierra el hueco de la auditoria: hoy nada vigila si un cierre cruza
el precio maximo de compra de un reporte aprobado.

Pasos:
1. Lee `data/watchlist.json` (sincronizado por `sync_publico.py` desde
   `app/frontend/public/data/watchlist.json`, generado por MER-F2H) --
   solo entradas con `estado == "vigente"`.
2. Para cada ticker, captura el cierre mas reciente (mismo metodo que
   `captura_diaria.py`: `yf.Ticker(ticker).history(period='5d', ...)`,
   ultimo Close no-cero). Si la captura de un ticker falla, se loguea un
   warning y se sigue con el resto -- un ticker problematico no debe tumbar
   el monitor completo.
3. Si `cierre <= precio_maximo_compra`: es un cruce. Se actualiza
   `data/alertas_historial.json` (estado interno, no consumido por el sitio)
   para contar `dias_consecutivos` -- se incrementa una vez por fecha nueva
   de cruce, nunca dos veces el mismo dia (idempotente); si el papel deja de
   estar en cruce, su racha se borra del historial.
4. Escribe `data/alertas.json` = `{"alertas": [...]}` con los cruces
   vigentes (`[]` si no hay ninguno) y una copia identica en
   `sitio/data/alertas.json` para que el banner del sitio ya buildeado (ver
   `sync_publico.inject_banner_alertas`) la sirva sin necesitar rebuild.

La alerta no es un error del pipeline: exit code 0 siempre, haya o no
cruces, y aunque algun ticker individual no se pueda capturar.

Uso: python3 scripts/monitor_watchlist.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

PUBLICO_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PUBLICO_DIR / "data"
SITIO_DATA_DIR = PUBLICO_DIR / "sitio" / "data"

WATCHLIST_JSON = DATA_DIR / "watchlist.json"
ALERTAS_JSON = DATA_DIR / "alertas.json"
ALERTAS_SITIO_JSON = SITIO_DATA_DIR / "alertas.json"
HISTORIAL_JSON = DATA_DIR / "alertas_historial.json"


def _leer_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _escribir_json(path, datos):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _capturar_cierre(ticker):
    """Retorna (fecha_iso, cierre) o (None, None) si no se pudo capturar.
    Mismo metodo que `captura_diaria.capturar_precios_holdings`: ultimo
    Close no-cero en `period='5d'`.
    """
    try:
        h = yf.Ticker(ticker).history(period="5d", interval="1d", auto_adjust=False, timeout=10)
    except Exception as e:  # noqa: BLE001 -- un ticker problematico no detiene el monitor
        print(f"WARNING: {ticker} fallo la captura via yfinance: {e}", file=sys.stderr)
        return None, None
    if h is None or h.empty:
        print(f"WARNING: {ticker} no devolvio datos en period='5d'.", file=sys.stderr)
        return None, None
    h.index = h.index.tz_localize(None) if h.index.tz is not None else h.index
    no_cero = h[h["Close"] > 0]
    if no_cero.empty:
        print(f"WARNING: todas las filas de {ticker} period='5d' tienen Close<=0.", file=sys.stderr)
        return None, None
    ultima = no_cero.iloc[-1]
    fecha_cierre = str(no_cero.index[-1].date())
    return fecha_cierre, float(ultima["Close"])


def _actualizar_racha(historial, ticker, fecha_cierre):
    """Actualiza (in-place) `dias_consecutivos` de un cruce vigente.
    Idempotente por fecha: si ya se registro un cruce para `ticker` en
    `fecha_cierre`, no se vuelve a incrementar.
    """
    registro = historial.get(ticker)
    if registro is not None and registro["ultima_fecha_cruce"] == fecha_cierre:
        return registro["dias_consecutivos"]
    if registro is not None:
        dias = registro["dias_consecutivos"] + 1
        primera = registro["primera_fecha_cruce"]
    else:
        dias = 1
        primera = fecha_cierre
    historial[ticker] = {
        "primera_fecha_cruce": primera,
        "ultima_fecha_cruce": fecha_cierre,
        "dias_consecutivos": dias,
    }
    return dias


def main():
    if not WATCHLIST_JSON.exists():
        print(f"ERROR: falta {WATCHLIST_JSON} (correr sync_publico.py primero, MER-F2H/F2I).", file=sys.stderr)
        # No es un error de pipeline detener el monitor si aun no hay watchlist
        # sincronizada (p.ej. antes de que exista el primer reporte aprobado);
        # se deja alertas.json vacio y se sale limpio.
        _escribir_json(ALERTAS_JSON, {"alertas": []})
        _escribir_json(ALERTAS_SITIO_JSON, {"alertas": []})
        sys.exit(0)

    watchlist = _leer_json(WATCHLIST_JSON, {"watchlist": []})["watchlist"]
    vigentes = [w for w in watchlist if w.get("estado") == "vigente"]

    historial = _leer_json(HISTORIAL_JSON, {})
    tickers_vigentes = {w["ticker"] for w in vigentes}
    for ticker in list(historial.keys()):
        if ticker not in tickers_vigentes:
            del historial[ticker]

    alertas = []
    for w in vigentes:
        ticker = w["ticker"]
        precio_maximo = w["precio_maximo_compra"]
        fecha_cierre, cierre = _capturar_cierre(ticker)
        if fecha_cierre is None:
            continue

        if cierre <= precio_maximo:
            dias = _actualizar_racha(historial, ticker, fecha_cierre)
            alertas.append({
                "ticker": ticker,
                "cierre": cierre,
                "precio_maximo": precio_maximo,
                "fecha": fecha_cierre,
                "dias_consecutivos": dias,
            })
            print(f"ALERTA: {ticker} cerro en {cierre:.2f} <= maximo {precio_maximo:.2f} ({fecha_cierre}, dia {dias}).")
        else:
            if ticker in historial:
                del historial[ticker]
            print(f"OK: {ticker} cerro en {cierre:.2f} > maximo {precio_maximo:.2f} ({fecha_cierre}).")

    _escribir_json(HISTORIAL_JSON, historial)
    alertas.sort(key=lambda a: a["ticker"])
    resultado = {"alertas": alertas}
    _escribir_json(ALERTAS_JSON, resultado)
    _escribir_json(ALERTAS_SITIO_JSON, resultado)

    generado_en = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"monitor_watchlist: {len(alertas)} cruce(s) vigente(s) de {len(vigentes)} papel(es) monitoreado(s) ({generado_en}).")
    print("monitor_watchlist OK.")
    sys.exit(0)


if __name__ == "__main__":
    main()
