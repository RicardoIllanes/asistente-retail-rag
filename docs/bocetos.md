# Bocetos de diseño

## 1. Interfaz de chat (propuesta para el sitio web)
```
┌──────────────────────────────────────────────┐
│  TecnoHogar · Asistente Tecno         ● 24/7 │
├──────────────────────────────────────────────┤
│ Tecno: ¡Hola! Soy Tecno. Puedo ayudarte con  │
│ pedidos, despachos, garantías y productos.   │
│                                              │
│             Tú: ¿dónde está mi TH-10245? ▸   │
│                                              │
│ Tecno: Tu pedido está DESPACHADO con Starken │
│ (ST55410). Entrega estimada: 25-09-2026.     │
│ ─ Fuentes: pedidos.csv §TH-10245             │
│                                              │
│ [Hablar con un ejecutivo]  [Ver mis pedidos] │
├──────────────────────────────────────────────┤
│ Escribe tu consulta...                  [➤]  │
└──────────────────────────────────────────────┘
```
Decisiones: citas visibles bajo cada respuesta (transparencia), botón permanente de derivación a humano.

## 2. Flujo de decisión del agente
```
consulta ─► enmascarar PII ─► ¿menciona pedido TH-XXXXX? ──sí──► consultar_pedido ─► ¿INCIDENCIA? ──sí──► derivar
                                   │no                                                    │no
                                   ▼                                                      ▼
                     ¿tema legal (garantía/retracto/retraso)? ──sí──► políticas + normativa ─► comparar ─► responder con citas
                                   │no
                                   ▼
                     ¿producto/precio/stock? ──sí──► catálogo ─► responder
                                   │no
                                   ▼
                     políticas internas ─► ¿SIN_RESULTADOS? ──sí──► reconocer límite y derivar
```

## 3. Diagramas
- `arquitectura.png` / `arquitectura.mmd`: componentes y su integración.
- `flujo_rag.png` / `flujo_rag.mmd`: secuencia de una consulta de principio a fin.
