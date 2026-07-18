# Meridiano

Meridiano es un ejercicio público y versionado de inversión value en el mercado
chileno, con capital **100% ficticio**. Cada decisión (entrada, salida,
mantención, revisión) se toma bajo una metodología explícita y se registra en
una bitácora de decisiones append-only, con una cadena de hashes que permite a
cualquiera verificar de forma independiente que el historial no fue alterado
después de publicado.

> ⚠ **Disclaimer:** Todo el contenido de Meridiano es educativo y documenta un
> ejercicio de inversión con capital 100% ficticio — ninguna cifra de
> portafolio representa dinero real. Nada de lo publicado aquí es asesoría de
> inversión, recomendación de compra o venta, ni una sugerencia para replicar
> en una cuenta real: son decisiones tomadas bajo una metodología pública y
> versionada, con supuestos explícitos que pueden estar equivocados y que de
> hecho fallarán en algunos casos — eso queda documentado, no escondido.
> Cualquiera que use este contenido para decidir con su propio dinero lo hace
> bajo su entero criterio y responsabilidad.

## Qué garantiza el log

`decision-log/log.jsonl` es un export append-only del `DecisionLog` interno:
un JSON por línea, en orden, donde cada fila incluye `hash_entrada` (hash de
su propio contenido + el hash de la fila anterior) y `hash_anterior`. Esto
forma una cadena: modificar o borrar cualquier fila pasada rompe el hash de
todas las filas posteriores. El historial de commits de este repositorio
público (con sus timestamps de GitHub, verificables independientemente de
Meridiano) es la capa 4 de verificación externa: cualquiera puede clonar este
repo en cualquier momento y confirmar que el log de hoy es una extensión
estricta del log de ayer.

## Cómo verificar la cadena

1. Clona este repo y abre `decision-log/log.jsonl` (un JSON por línea,
   append-only).
2. Parte de `hash_anterior` = `SHA-256("meridiano-genesis")` para la primera
   fila.
3. Para cada fila en orden: verifica que `hash_anterior` == el `hash_entrada`
   de la fila anterior.
4. Recalcula `hash_entrada` = `SHA-256(id + timestamp_real + tipo_evento +
   descripcion + hash_anterior)` y compáralo con el valor publicado.
5. Si alguna fila no calza, la cadena está rota desde ese punto — repórtalo,
   es el punto de esta verificación.

```python
import hashlib, json
GENESIS = hashlib.sha256(b"meridiano-genesis").hexdigest()
prev = GENESIS
for linea in open("decision-log/log.jsonl", encoding="utf-8"):
    f = json.loads(linea)
    assert f["hash_anterior"] == prev, f"cadena rota en id={f['id']}"
    partes = [f["id"], f["timestamp_real"], f["tipo_evento"], f["descripcion"], f["hash_anterior"]]
    calc = hashlib.sha256("".join(str(p) for p in partes).encode("utf-8")).hexdigest()
    assert calc == f["hash_entrada"], f"hash no coincide en id={f['id']}"
    prev = f["hash_entrada"]
print("cadena OK")
```

## Contenido de este repo

- `decision-log/log.jsonl` — bitácora de decisiones, append-only (ver arriba).
- `reportes/` — informes de valoración `.md` de cada activo aprobado por el
  gestor antes de cualquier transacción.
- `data/` — capturas diarias (nivel IPSA vivo, cierres de los holdings, UF).
- `sitio/` — el sitio estático servido en producción (generado, no editado a
  mano).
- `scripts/` — captura diaria y guard de publicación (código no sensible).
- `.github/workflows/diario.yml` — automatización que corre cada día hábil.

## Actualización diaria

Un GitHub Action (`.github/workflows/diario.yml`) corre cada día hábil:
captura el nivel IPSA vivo, los cierres de los holdings y la UF del día,
recalcula la serie de NAV, regenera los JSON del sitio, commitea si hay
cambios (con el timestamp de GitHub como sello externo verificable) y
sincroniza el sitio a producción.
