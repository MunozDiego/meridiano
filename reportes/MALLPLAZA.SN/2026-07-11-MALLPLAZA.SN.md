# Reporte de valoración — Plaza S.A. (MALLPLAZA.SN)

Todos los números de este reporte salen de `codigo/valoracion.py` y su JSON
(`2026-07-11-MALLPLAZA.SN.json`); las fuentes están en `codigo/fuentes.md`.
Verificación mecánica: `codigo/check_consistencia.py`.

## 0. Metadatos y trazabilidad

- Empresa / ticker: Plaza S.A. / MALLPLAZA.SN (Bolsa de Santiago)
- Fecha y hora del reporte (timestamp real de la decisión): **2026-07-11** (sesión Cowork MER-F1I)
- Precio de cierre usado y fecha: **CLP 3.900,00** (2026-07-09, `precios.parquet`)
- Versión del framework: v1.0 (Fase 0, Paso 2)
- **Flag de método:** `BASELINE` (el MoS dinámico H2 se publica EN PRUEBA / experimental,
  en paralelo y sin peso decisional; RESULTADOS-v1 citados en §5 y §8)
- Autor/modelo: Claude (Fable), ejecutor `cowork` — **revisión humana pendiente: Diego
  debe aprobar este reporte antes de que MER-F1K lo use** (tarea registrada en Cortex)

## 1. Higiene de datos (checklist obligatorio de 1d)

- [x] `financialCurrency` verificado: **CLP** (fundamentales.csv, FY2022-FY2025; fx_usado=1,0)
- [x] EPS recalculado desde Net Income / Shares: 1.431.012 MM / 2.190 MM = **653,43 CLP**
      — coincide con el reportado, pero está **CONTAMINADO por fair value**: la utilidad
      2025 incluye MMCLP 1.448.943 de revalorización de propiedades de inversión (IAS 40).
      EPS ex fair value = 369.312/2.190 = **168,6 CLP**. Ídem el **EBITDA yfinance 2025
      (1.935.928): incluye el fair value**; el modelo usa el EBITDA reportado por la
      compañía **ex fair value (526.228)**. Nota metodológica completa: `fuentes.md §9`.
- [x] Fuente y profundidad de fundamentales: yfinance 4 años (FY2022-25) + release 4T25 y
      análisis razonado oficiales (serie EBITDA compañía 2021-25)
- [x] Benchmark usado: benchmark sintético equiponderado del proyecto (proxy declarado;
      el ^IPSA de Yahoo está muerto — 1d hallazgo #1)

## 2. Filtro de primer orden — profitabilidad

- GP/A (proxy screening EBITDA/Capital invertido): actual 0,3185, promedio 3a **0,1843**
  vs mediana del universo 0,0932 → **pasa el filtro** (percentil 87,2%). El filtro
  mecánico ya operó en FASE-1F; se declara que la cifra 2025 de esa base incluye fair
  value — recalculado sobre EBITDA ex FV 2025: 526,2/(4.482,9+1.595,4−268,3) ≈ **9,1%**,
  apenas bajo la mediana (9,32%). La rentabilidad **operacional** de Mallplaza es real
  (margen EBITDA 80,5%, el mejor del sector local), pero medida sobre activos a fair
  value ya no es sobresaliente: los tasadores capitalizaron la renta dentro del activo.

## 3. Tesis (máximo 5 líneas)

Mallplaza es el mejor operador de malls de la región andina (ocupación 95,9%, margen
EBITDA 80,5%, contratos a 6,7 años 93% fijos e indexados, DFN/EBITDA 2,5x) y su
integración de Perú fue un éxito operativo. Pero a CLP 3.900 el mercado paga ~19x
EV/EBITDA, ~21x FFO y **1,9x el NAV de tasación**: el precio ya incorpora la ejecución
perfecta del plan de crecimiento. El DCF baseline (V central post-iliquidez ≈ **3.107**)
deja retorno esperado central **negativo**; no hay margen de seguridad a este precio.

## 4. Valoración

### 4.1 DCF (método primario)

- **WACC CLP desglosado:** Rf_CLP = 5,50% (BTP-10, TradingEconomics 22-jun-2026) |
  β_u = 0,50 bottom-up real estate rentas/REIT EM → β_L = 0,556 (D/E 0,153) |
  ERP madura = 4,23% (Damodaran ene-2026) | **λ = 0,72** (ingresos Chile 72,2% del
  consolidado — release 4T25) | CRP = 1,10% (Damodaran, edición 5-ene-2026) →
  Ke = 8,64%; Kd after-tax = 4,31% (tasa promedio deuda 2,98%, 82% UF); pesos E 86,7% /
  D 13,3% → **WACC = 8,07%**.
  Contraste declarado: β de regresión local = **1,01** (60 meses vs benchmark sintético)
  — muy por sobre el bottom-up, inflado por el período de re-rating 2024-25 (aumento de
  capital, MSCI/FTSE, +95% en 12m). Con β=1,01 el Ke sería ~10,6% y todo el rango V
  bajaría; el pesimista (WACC +100 pb) cubre parte de esa divergencia. Se mantiene el
  bottom-up como primario por regla 2d (β de sector, sin Total Beta) y se declara.
- **Supuestos de proyección 2026-2030** (base EBITDA ex FV 526,2 MMM; fuentes §1):
  crecimiento EBITDA pesimista 3,5% / central 5,5% / optimista 7,5% — ancla: orgánico
  1T26 +5,2%, SSR 5-6%, plan +168.600 m² GLA (+7,2%) a 2028; capex del plan USD 578,5 MM
  remanentes → ~160-175 MMM CLP/año 2026-28, cayendo a mantenimiento+reconversión después;
  ΔWC −5 MMM/año; **impuestos FCFF: pesimista 27% (estatutaria) / central 18% / optimista
  14%** — la tasa de caja observada es 12,1% del EBIT (impuestos corrientes 63,0 vs gasto
  contable 428,0, cuyo grueso es diferido por fair value); el central asume erosión
  gradual del escudo, el pesimista su desaparición. Supuesto declarado, no silencioso.
- **Valor terminal:** Gordon sobre FCFF terminal con capex normalizado (18% del EBITDA);
  g terminal 3,0% / 3,5% / 4,0% nominal (≈ inflación 2,9% + 0,1-1,1 real). Fragilidad de
  g declarada (Ohlson): con WACC−g de solo 4,5 pp en el central, el TV es ~75% del EV —
  la sensibilidad es alta y es la razón de publicar rango y no punto.
- **Rango de valor intrínseco (CLP/acción): pesimista 1.584 / central 3.108 / optimista 4.875**
  (equity = EV − DFN 1.311 − minoritarios 42; EV central 8.158 MMM = 15,5x EBITDA-25).
- **Sensibilidad ESF obligatoria (estrés):** EBITDA −15% permanente, t=27%, WACC +100 pb,
  g=0, capex solo mantenimiento → **V ≈ 613 CLP/acción**. Es deliberadamente punitivo
  (perpetuidad sin crecimiento sobre flujos castigados); el piso económico real en estrés
  lo daría la venta de activos contra un NAV de tasación de ~2.047 CLP/acción, que en
  crisis también se tasaría a la baja. Ambos números se publican como referencia de cola.

### 4.2 Múltiplos de contraste

- Comp-set local (≥4, calculados desde datos del proyecto): PARAUCO.SN (P/E 24,4,
  EV/EBITDA 15,8), CENCOMALLS.SN (12,7 / 11,5), FALABELLA.SN (10,9 / 4,4 — contexto,
  conglomerado) y CENCOSUD.SN (18,0 / 12,9 — contexto). Advertencia: PARAUCO y
  CENCOMALLS también aplican IAS 40, sus múltiplos yfinance arrastran fair value.
- Múltiplos propios vs percentil histórico PROPIO (screening, profundidad 4 años):
  P/E 4,88 pct 25% y EV/EBITDA-norm 8,46 pct 25% — **ambos contaminados por fair value**
  (declarado); **P/B 1,56 = percentil 100** (el único limpio de los tres: patrimonio a
  valor de tasación). Múltiplos limpios calculados hoy: **P/E ex FV 23,1x | P/FFO 21,1x |
  EV/EBITDA ex FV 18,8x | P/NAV de tasación 1,91x**.
- **Regla de Estrada:** el múltiplo en cuartil extremo es P/B (percentil 100 propio) y
  apunta CARO, no barato. ¿Contradice el DCF? No: lo confirma — el DCF central implica
  15,5x EBITDA vs 18,8x de mercado. El "barato" del screening era un artefacto del fair
  value en el denominador (exactamente el mecanismo de H2b: normalizar deshace la señal).
  No corresponde recorte de V por banda de múltiplos (el DCF ya está BAJO el mercado).
- Utilidades normalizadas vs punto del ciclo: no es commodity/USD; la "normalización"
  relevante aquí es ex fair value, aplicada en toda la valoración.

## 5. Ajustes específicos del mercado chileno

- **Iliquidez [BASELINE — costo]:** Amihud_i = 0,006860 (×1e9, mediano 3a) | S = CLP 10 MM
  (10% del NAV ficticio) | n = 3 años | r = WACC 8,07% → **D_i = (Amihud×S)/(r×n) =
  0,03%** (c round-trip ≈ CLP 686 por cada 10 MM; tope 25% lejos) | V central post-D_i =
  **3.107**. Mallplaza es hoy de lo más líquido del universo (ADTV 180d ≈ USD 10 MM,
  MSCI/FTSE); el costo de ejecución es inmaterial para este tamaño. Per RESULTADOS-v1,
  H1 tiene evidencia en contra: D_i se usa solo como costo, no como fuente de retorno.
- **Gobierno corporativo:** controlador **Falabella S.A. 53,05%** (grupo Solari/Said;
  la familia fundadora Müller conserva ~11,4% tras vender) | AFP 24,42% (dic-2025;
  18,81% en feb-2025) | serie única de acciones | historial de conflictos con
  minoritarios: **sin episodios documentados**; la compra de Falabella Perú (2024) fue
  operación entre relacionadas cursada por OPA → sin recargo MoS | dilución por
  compensación >3% (regla Graham/Zweig): **no** (sin programas de opciones relevantes;
  el aumento de capital 2024 fue por la adquisición, suscrito). Riesgo estructural
  declarado: dependencia comercial del grupo controlador (Falabella/Sodimac/Tottus son
  arrendatarios ancla) — alinea intereses pero concentra contraparte.
- **Contexto de flujos AFP [H3 DESCARTADA — solo descriptivo]:** las AFP subieron de
  18,8% a 24,4% durante 2025, comprando en la ventana del re-rating y la entrada a MSCI.
  Flujo comprador reciente relevante; sin peso decisional (H3 descartada en RESULTADOS-v1,
  con su caveat de fuente delgada).
- Si es holding: no aplica (Plaza S.A. es operadora; el contraste NAV va en §4.2).

## 6. Margen de seguridad

- **MoS estático [BASELINE — decide]:** m = 25% base + 0 (Amihud pct 41,9%, no tercil
  superior) + 0 (no cíclico/commodity) + 0 (sin conflictos documentados) = **25%**
- **Precio máximo de compra = (1−0,25) × 3.107 = CLP 2.330**
- **MoS dinámico [H2 EN PRUEBA — se publica, no decide; α degradado por T4]:**
  DY ejercicio 2025 = 1,74% | α asumido = 0,15 | c/n ≈ 0,00 → **MoS_min = 40,6%** —
  exigiría comprar bajo ~1.845. La lectura del "reloj": con carry de 1,7% (screening:
  1,3% sostenible), esperar convergencia aquí casi no paga — un value sin dividendo
  exige el descuento grande que el precio actual no ofrece ni de lejos.
- ¿P actual (3.900) cumple el MoS estático? **NO** (excede el precio máximo en +67%).

## 7. Catalizadores y reloj

- Catalizadores identificados (con horizonte): apertura de ~168.600 m² GLA 2026-2028
  (Vespucio 2S26, Oeste/Trujillo 2S26, Trébol/Angamos 1S27, La Serena/La Marina 2S27);
  maduración de los premium outlets (Biobío dic-25, Atocongo 1S26); estrategia
  residencial (10.000 viviendas potenciales, 2.000 en ejecución — opcionalidad a 3-5
  años); posible aumento de payout al terminar el capex pesado (post-2028). Nota: son
  catalizadores de crecimiento del NEGOCIO ya pagados por el precio, no de cierre de
  descuento — no hay descuento que cerrar.
- Rol del dividendo como carry: DY 1,74% vs Rf 5,50% → **carry negativo de −3,8 pp
  contra la renta fija local**; el reloj corre en contra mientras se espera.
- Fecha de revisión forzada: **2028-07-11** (reporte + 24 meses).

## 8. Riesgos y falsación de la tesis (ex-ante)

La "tesis" operativa de este reporte es **NO comprar a este precio** (§10). Riesgos y
condiciones en ambas direcciones:

- Riesgos del negocio (para quien compre hoy): (i) tasa — con TV ~75% del EV, +100 pb de
  WACC mueven el central de 3.108 a ~2.4xx (ver pesimista); (ii) reversión del escudo
  tributario de caja (12%→27% recorta el FCFF ~18%); (iii) desaceleración del consumo
  andino (Perú/Colombia = 28% del ingreso); (iv) e-commerce y obsolescencia de formatos
  (mitigado por conversión a "centros urbanos", pero el capex de reconversión es
  permanente); (v) concentración de anclas del grupo Falabella; (vi) ejecución del plan
  (USD 578 MM) con retornos incrementales menores a los históricos.
- **Qué falsificaría el "no comprar" (condiciones observables que obligan a revalorar):**
  (1) precio ≤ CLP 2.330 (el máximo de compra baseline) sin deterioro del EBITDA ex FV;
  (2) EBITDA ex FV creciendo >8%/año por dos años consecutivos (2026-2027) con margen
  ≥80% — el optimista se vuelve central y V central ≈ 4.9xx;
  (3) cambio de política de dividendos a payout ≥60% (DY ≥4% al precio de hoy) — cambia
  el reloj H2 y el MoS dinámico cae de 40,6% a ~25%;
  (4) evidencia de que el escudo tributario de caja es permanente (t≈12-14% sostenida
  por 3+ ejercicios) — movería el central hacia ~3.5xx.
  Cualquiera de estas cuatro dispara re-valoración formal antes de la revisión forzada.

## 9. Retorno esperado (anualizado a 3 años, incluye DY 1,74%)

| Escenario | CLP nominal | UF-real |
|---|---|---|
| Pesimista (V post-D_i 1.584) | **−24,2%** | −26,3% |
| Central (V post-D_i 3.107) | **−5,6%** | −8,2% |
| Optimista (V post-D_i 4.874) | **+9,5%** | +6,4% |

La brecha nominal-real usa la inflación implícita BTP10−BTU10 (2,9%). Solo el escenario
optimista supera al BTU-10 (2,52% real) — y ni siquiera él supera el hurdle de 12%.

## 10. DecisionLog

- **Recomendación: NO COMPRAR a CLP 3.900.** Empresa de primera calidad a precio de
  perfección: sin margen de seguridad (precio máximo baseline: **CLP 2.330**), carry
  negativo vs renta fija, y el único escenario con retorno positivo es el optimista.
  Queda en watchlist con las condiciones de falsación de §8 como gatillos.
- Tamaño propuesto: **0% del NAV** (sin transacción). Referencia de límites si algún día
  entrara: min(12% NAV = CLP 12 MM; 1 día de volumen mediano 60d ≈ CLP 1.394 MM 3a,
  hoy ~CLP 9.400 MM) → la liquidez no restringe.
- Timestamp del registro: 2026-07-11 (este archivo, publicado ANTES de cualquier
  transacción simulada — no la hay).
- Video asociado: no aplica (Fase 1N pendiente).

---

*Método BASELINE del framework v1.0. Las hipótesis propias H1-H4 siguen EN PRUEBA o
descartadas según `estrategias/backtests/v1/RESULTADOS-v1.md` (H1 en contra → D_i solo
costo; H2c en contra → MoS dinámico publicado como experimental y degradado a
"dividendos + costo"; H2b a favor → la normalización ex fair value que este reporte
aplica; H3 descartada → flujos AFP solo contexto). Nada de lo anterior se usó con peso
decisional fuera del baseline.*

APROBADO: MALLPLAZA.SN — 2026-07-14 — Diego
