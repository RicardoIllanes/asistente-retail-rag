# Evidencia de pruebas

Fecha de ejecución: 25-09-2026 · Python 3 · Chroma · embeddings `local` (léxicos) para reproducibilidad sin costo.

## 1. Pruebas automatizadas (`pytest -v`)
```
tests/test_agent.py::test_agente_usa_herramienta_y_registra_traza PASSED [  6%]
tests/test_guardrails_memory.py::test_enmascara_datos_personales PASSED  [ 12%]
tests/test_guardrails_memory.py::test_codigo_pedido_no_se_enmascara PASSED [ 18%]
tests/test_guardrails_memory.py::test_memoria_ventana_deslizante_y_hechos PASSED [ 25%]
tests/test_ingest.py::test_chunks_respetan_tamano_y_tienen_metadatos PASSED [ 31%]
tests/test_ingest.py::test_catalogo_un_documento_por_producto PASSED     [ 37%]
tests/test_ingest.py::test_separacion_fuentes_internas_y_externas PASSED [ 43%]
tests/test_retriever.py::test_recupera_politica_de_despachos PASSED      [ 50%]
tests/test_retriever.py::test_recupera_normativa_retracto PASSED         [ 56%]
tests/test_retriever.py::test_umbral_descarta_consultas_fuera_de_dominio PASSED [ 62%]
tests/test_retriever.py::test_resultados_ordenados_por_score PASSED      [ 68%]
tests/test_retriever.py::test_contexto_incluye_fuente_para_trazabilidad PASSED [ 75%]
tests/test_tools.py::test_consultar_pedido_existente PASSED              [ 81%]
tests/test_tools.py::test_consultar_pedido_inexistente PASSED            [ 87%]
tests/test_tools.py::test_buscar_catalogo_solo_devuelve_productos PASSED [ 93%]
tests/test_tools.py::test_traza_registra_fuentes PASSED                  [100%]
============================== 16 passed in 0.39s ==============================
```
Cobertura: chunking y metadatos, separación de fuentes internas/externas, recuperación y umbral,
herramientas del agente, trazabilidad, enmascarado de datos personales, memoria conversacional y
bucle de tool-calling con LLM simulado.

## 2. Métricas de recuperación (`python -m eval.evaluate --provider local --k K`)
18 preguntas con fuentes relevantes etiquetadas manualmente (`eval/dataset.json`).

| top-k | Hit rate | Context precision | Context recall | MRR |
|---|---|---|---|---|
| 2 | 0.944 | 0.861 | 0.917 | 0.944 |
| 4 | 0.944 | 0.824 | 0.917 | 0.944 |
| 6 | 0.944 | 0.817 | 0.917 | 0.944 |

Experimento de chunking (k=4): con chunk 300/50 se obtiene recall 0.944 pero precisión 0.782 (más fragmentos
cortos compiten); con 700/120 precisión 0.824 y recall 0.917. Se eligió 700/120 porque las secciones de las
políticas caben completas en un chunk y se mantiene el contexto semántico.

### Detalle por pregunta (k=4)
| ID | Pregunta | Hit | Precisión | Recall | Primer fragmento (score) |
|---|---|---|---|---|---|
| Q01 | ¿Cuántos meses de garantía legal tiene un producto nuevo? | ✔ | 1.0 | 1.0 | politica_garantias.md§1. Garantía legal (6 meses) (0.434) |
| Q02 | Mi lavadora falló, ¿puedo pedir la devolución del dinero en vez de la reparación? | ✔ | 1.0 | 0.5 | sernac_guia_compras_online.md§Regla del 6x3 (0.249) |
| Q03 | ¿Cuántos días tengo para devolver una compra online por arrepentimiento? | ✔ | 0.67 | 1.0 | politica_garantias.md§5. Devolución por arrepentimiento (compras online) (0.239) |
| Q04 | ¿Qué dice la ley sobre el derecho a retracto en compras por internet? | ✔ | 0.25 | 1.0 | ley_19496_extracto.md§Derecho a retracto en compras a distancia (artículo 3 bis) (0.343) |
| Q05 | ¿Cuánto demora el despacho a Magallanes? | ✔ | 1.0 | 1.0 | politica_despachos.md§3. Costos (0.134) |
| Q06 | ¿El despacho es gratis en la Región Metropolitana? | ✔ | 0.67 | 1.0 | politica_despachos.md§3. Costos (0.387) |
| Q07 | ¿Qué pasa si mi pedido se retrasa más del plazo informado? | ✔ | 1.0 | 1.0 | politica_despachos.md§6. Retrasos (0.274) |
| Q08 | El proveedor no cumplió el plazo de entrega, ¿qué derechos tengo según SERNAC? | ✔ | 1.0 | 1.0 | sernac_guia_compras_online.md§Plazos de despacho (0.395) |
| Q09 | ¿Puedo pagar en cuotas sin interés? | ✔ | 1.0 | 1.0 | preguntas_frecuentes.md§Medios de pago (0.268) |
| Q10 | ¿Puedo cambiar la boleta por factura después de comprar? | ✔ | 1.0 | 1.0 | preguntas_frecuentes.md§Boleta y factura (0.474) |
| Q11 | ¿Cuál es el precio del refrigerador No Frost de 340 litros? | ✔ | 1.0 | 1.0 | catalogo_productos.csv§TH-RF340 (0.473) |
| Q12 | ¿Hay stock de la lavadora de carga frontal de 12 kg? | ✔ | 1.0 | 1.0 | catalogo_productos.csv§TH-LV12 (0.567) |
| Q13 | ¿Cuánto cuesta el retiro si devuelvo un producto por arrepentimiento? | ✔ | 1.0 | 1.0 | politica_garantias.md§5. Devolución por arrepentimiento (compras online) (0.239) |
| Q14 | Mi televisor llegó dañado por el transporte, ¿qué hago? | ✘ | 0.0 | 0.0 | — |
| Q15 | ¿El courier es responsable si el producto llega roto o lo es la tienda? | ✔ | 1.0 | 1.0 | sernac_guia_compras_online.md§Productos dañados en el traslado (0.339) |
| Q16 | ¿Dónde está la tienda física y en qué horario atiende? | ✔ | 1.0 | 1.0 | preguntas_frecuentes.md§Tienda física (0.335) |
| Q17 | ¿Cuánto demora el reembolso de mi dinero? | ✔ | 1.0 | 1.0 | politica_garantias.md§6. Reembolsos (0.152) |
| Q18 | ¿Puedo cambiar la dirección de despacho de mi pedido? | ✔ | 0.25 | 1.0 | preguntas_frecuentes.md§Cambio de dirección de despacho (0.396) |

**Análisis de la falla Q14:** "Mi televisor llegó dañado por el transporte" sí ubica en primer lugar el fragmento
correcto (`politica_despachos.md §5. Incidencias`), pero con score 0.082, bajo el umbral de 0.12, por lo que se
descarta. Solo coinciden 2 palabras ("dañado", "transporte"); "llegó" ≠ "llega" para un embedding léxico. Muestra
el compromiso del umbral: subirlo reduce ruido (precisión), bajarlo mejora recall. Con embeddings semánticos
(Gemini) la similitud entre variaciones morfológicas es mayor, por eso se usan en producción.

## 3. Demo de recuperación (`python -m eval.demo_recuperacion`)
```
Consulta: Mi lavadora falló a los 3 meses, ¿me devuelven el dinero?

== Colección internos ==
  score=0.176  catalogo_productos.csv §TH-LV12
  score=0.145  politica_garantias.md §3. Garantía extendida TecnoHogar Plus
  score=0.132  catalogo_productos.csv §TH-TV55
  score=0.132  politica_despachos.md §2. Plazos estimados (días hábiles desde la confirmación del pago)

== Colección externos ==
  score=0.15   sernac_guia_compras_online.md §Regla del 6x3

```
Con embeddings léxicos, la palabra "falló" no coincide con "falla", por lo que la política interna de garantía
legal no aparece; la fuente externa (Regla del 6x3) sí. Esto muestra por qué el agente consulta ambas
colecciones en temas legales y por qué se recomiendan embeddings semánticos.

## 4. Pruebas con Gemini (ejecutadas el 25-09-2026 en Windows, Python 3.14)

### Recuperación con `gemini-embedding-001` (`python -m eval.evaluate`, k=4, umbral 0.55)
| Métrica | Local (léxico) | Gemini (semántico) |
|---|---|---|
| Hit rate | 0.944 | **1.000** |
| Context precision | 0.824 | 0.681 |
| Context recall | 0.917 | **1.000** |
| MRR | 0.944 | **1.000** |

Con embeddings semánticos se recuperó la fuente correcta en primer lugar en las 18 preguntas, incluida Q14
("llegó dañado"), que fallaba con el embedding léxico. La precisión baja porque con umbral 0.55 casi siempre pasan
los 4 fragmentos (algunos de secciones vecinas); subir el umbral o reducir k la mejoraría a costa de recall.

### Conversaciones con el agente (`python -m src.app --debug`, modelo gemini-3.8-flash)
**Consulta:** ¿Cuál es el estado de mi pedido TH-10245?
```
Tecno: Tu pedido TH-10245 se encuentra en estado DESPACHADO.
- Producto: TH-NB14 · Transportista: Starken (seguimiento ST55410)
- Destino: Región de Valparaíso · Fecha estimada de entrega: 25 de septiembre de 2026
Fuentes: pedidos.csv §TH-10245
  [herramientas] ['consultar_pedido']
  [fuente] pedidos.csv §TH-10245 (score=1.0)
```
Todos los datos coinciden con el registro de `pedidos.csv` (fidelidad total) y se cita la fuente.

**Consulta con código inexistente:** ¿Cuál es el estado de mi pedido TH_10425?
```
Tecno: No encontré registros para el pedido TH-10425. Te sugiero verificar el número [...]
Si el código es correcto y el error persiste, puedo derivarte con un ejecutivo humano [...]
Fuentes: ninguna
  [herramientas] ['consultar_pedido', 'buscar_politicas_internas']
```
El agente no inventa un estado: reconoce SIN_RESULTADOS y ofrece derivación, como exige el prompt.

### Fidelidad con LLM-as-judge (`--generacion`)
No se completó: la capa gratuita de Gemini devolvió errores 503 (alta demanda) y 429 (cuota agotada) durante las
pruebas. Se agregaron reintentos (`max_retries`) y manejo de errores para que el chat y la evaluación no se
interrumpan. Queda como trabajo pendiente con un plan de pago o en horario de menor demanda.
