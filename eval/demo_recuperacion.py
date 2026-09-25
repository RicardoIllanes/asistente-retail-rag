"""Muestra qué fragmentos se recuperan para una consulta (sin LLM). Útil para demostrar la trazabilidad.

    python -m eval.demo_recuperacion "¿cuánto demora el despacho a Magallanes?"
"""
import sys

from src.retriever import Recuperador

consulta = " ".join(sys.argv[1:]) or "Mi lavadora falló a los 3 meses, ¿me devuelven el dinero?"
rec = Recuperador()
print(f"Consulta: {consulta}\n")
for coleccion in ("internos", "externos"):
    print(f"== Colección {coleccion} ==")
    frags = rec.buscar(consulta, coleccion)
    if not frags:
        print("  (sin fragmentos sobre el umbral)")
    for f in frags:
        print(f"  score={f.score:<6} {f.cita()}")
    print()
