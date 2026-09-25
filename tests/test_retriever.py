from src.retriever import formatear_contexto


def test_recupera_politica_de_despachos(recuperador):
    frags = recuperador.buscar("plazo de despacho a Magallanes", "internos")
    assert frags and frags[0].fuente == "politica_despachos.md"


def test_recupera_normativa_retracto(recuperador):
    frags = recuperador.buscar("derecho a retracto compras por internet", "externos")
    # con embeddings léxicos el artículo aparece dentro del top-k (no necesariamente 1°)
    assert any(f.fuente == "ley_19496_extracto.md" and "3 bis" in f.seccion for f in frags)


def test_umbral_descarta_consultas_fuera_de_dominio(recuperador):
    assert recuperador.buscar("receta de empanadas de pino", "internos", umbral=0.12) == []


def test_resultados_ordenados_por_score(recuperador):
    frags = recuperador.buscar("garantía legal falla de fabricación", "internos", umbral=0.0)
    scores = [f.score for f in frags]
    assert scores == sorted(scores, reverse=True)


def test_contexto_incluye_fuente_para_trazabilidad(recuperador):
    frags = recuperador.buscar("medios de pago cuotas", "internos")
    ctx = formatear_contexto(frags)
    assert 'fuente="preguntas_frecuentes.md"' in ctx and "score=" in ctx
    assert formatear_contexto([]).startswith("SIN_RESULTADOS")
