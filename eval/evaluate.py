"""Evaluación del pipeline RAG.

Recuperación (sin costo, funciona con --provider local o gemini):
    python -m eval.evaluate --provider local
    - Hit rate@k        : % de preguntas con al menos una fuente relevante recuperada.
    - Context precision : fragmentos relevantes recuperados / fragmentos recuperados.
    - Context recall    : fuentes relevantes recuperadas / fuentes relevantes esperadas.
    - MRR               : posición del primer fragmento relevante (1/rango).

Generación (requiere GOOGLE_API_KEY):
    python -m eval.evaluate --generacion
    - Fidelidad (faithfulness) con LLM-as-judge: % de afirmaciones sustentadas en el contexto.
    - Citas: % de respuestas que incluyen la línea "Fuentes:".
"""
import argparse
import json
from pathlib import Path

from src import config
from src.ingest import indexar
from src.retriever import Recuperador

DATASET = Path(__file__).parent / "dataset.json"
RESULTADOS = Path(__file__).parent / "resultados"


def evaluar_recuperacion(provider: str | None, k: int, umbral: float, reindexar: bool = True) -> dict:
    if reindexar:
        indexar(provider)
    rec = Recuperador(provider)
    umbral = rec.umbral if umbral is None else umbral
    casos = json.loads(DATASET.read_text(encoding="utf-8"))
    filas, hits, precisiones, recalls, rr = [], 0, [], [], []
    for c in casos:
        frags = rec.buscar(c["pregunta"], c["coleccion"], k=k, umbral=umbral)
        fuentes = [f.fuente for f in frags]
        relevantes = set(c["fuentes_relevantes"])
        n_rel = sum(1 for f in fuentes if f in relevantes)
        precision = n_rel / len(fuentes) if fuentes else 0.0
        recall = len(relevantes & set(fuentes)) / len(relevantes)
        rango = next((i for i, f in enumerate(fuentes, 1) if f in relevantes), None)
        hits += 1 if rango else 0
        precisiones.append(precision)
        recalls.append(recall)
        rr.append(1 / rango if rango else 0.0)
        filas.append({"id": c["id"], "pregunta": c["pregunta"], "recuperadas": [f"{f.fuente}§{f.seccion} ({f.score})" for f in frags],
                      "precision": round(precision, 2), "recall": round(recall, 2), "hit": bool(rango)})
    n = len(casos)
    return {
        "provider": provider or config.EMBEDDINGS_PROVIDER, "k": k, "umbral": umbral, "n_preguntas": n,
        "hit_rate": round(hits / n, 3), "context_precision": round(sum(precisiones) / n, 3),
        "context_recall": round(sum(recalls) / n, 3), "mrr": round(sum(rr) / n, 3), "detalle": filas,
    }


def evaluar_generacion() -> dict:
    from src.agent import AgenteAtencion, crear_llm
    from src.prompts import JUDGE_PROMPT

    juez = crear_llm()
    casos = json.loads(DATASET.read_text(encoding="utf-8"))
    filas, fidelidades, con_citas = [], [], 0
    for c in casos:
        agente = AgenteAtencion()  # memoria nueva por pregunta
        try:
            r = agente.responder(c["pregunta"])
            contexto = "\n".join(t["contenido"] for t in r.traza) or "(vacío)"
            veredicto = juez.invoke(JUDGE_PROMPT.format(contexto=contexto, respuesta=r.texto)).content
        except Exception as e:  # 503/429 de la API: se omite la pregunta y se informa
            print(f"  {c['id']}: omitida por error de la API ({str(e)[:80]})")
            filas.append({"id": c["id"], "pregunta": c["pregunta"], "error": str(e)[:200]})
            continue
        if not isinstance(veredicto, str):
            veredicto = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in veredicto)
        try:
            datos = json.loads(veredicto.strip().removeprefix("```json").removesuffix("```").strip())
            fid = float(datos.get("fidelidad", 0))
        except (json.JSONDecodeError, ValueError):
            datos, fid = {"error": veredicto}, 0.0
        fidelidades.append(fid)
        cita = "Fuentes:" in r.texto
        con_citas += cita
        print(f"  {c['id']}: fidelidad={fid} cita={'sí' if cita else 'no'}")
        filas.append({"id": c["id"], "pregunta": c["pregunta"], "respuesta": r.texto,
                      "herramientas": r.herramientas_usadas, "fidelidad": fid, "cita_fuentes": cita, "juez": datos})
    n = max(len(fidelidades), 1)
    print(f"  Preguntas evaluadas: {len(fidelidades)} de {len(casos)}")
    return {"fidelidad_promedio": round(sum(fidelidades) / n, 3), "tasa_citas": round(con_citas / n, 3), "detalle": filas}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", choices=["gemini", "local"], default=None)
    p.add_argument("--k", type=int, default=config.TOP_K)
    p.add_argument("--umbral", type=float, default=None, help="por defecto, el del proveedor")
    p.add_argument("--generacion", action="store_true")
    a = p.parse_args()
    RESULTADOS.mkdir(exist_ok=True)
    if a.generacion:
        res = evaluar_generacion()
        nombre = "generacion.json"
        print(f"Fidelidad promedio: {res['fidelidad_promedio']} | Respuestas con citas: {res['tasa_citas']}")
    else:
        res = evaluar_recuperacion(a.provider, a.k, a.umbral)
        nombre = f"recuperacion_{res['provider']}_k{a.k}.json"
        print(f"[{res['provider']}] k={a.k} umbral={a.umbral} | Hit rate: {res['hit_rate']} | "
              f"Context precision: {res['context_precision']} | Context recall: {res['context_recall']} | MRR: {res['mrr']}")
    (RESULTADOS / nombre).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resultados guardados en eval/resultados/{nombre}")


if __name__ == "__main__":
    main()
