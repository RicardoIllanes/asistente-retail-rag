"""Recuperación: búsqueda por similitud con umbral de relevancia y formateo con citas."""
from dataclasses import dataclass
from pathlib import Path

from langchain_chroma import Chroma

from src import config
from src.embeddings import get_embeddings


@dataclass
class Fragmento:
    contenido: str
    fuente: str
    seccion: str
    tipo_fuente: str
    version: str
    score: float

    def cita(self) -> str:
        return f"{self.fuente} §{self.seccion}"


class Recuperador:
    def __init__(self, provider: str | None = None, directorio: Path | None = None):
        emb = get_embeddings(provider)
        self.umbral = {"local": 0.12}.get(provider, config.SCORE_THRESHOLD) if provider else config.SCORE_THRESHOLD
        directorio = str(directorio or config.VECTOR_DIR)
        self.colecciones = {
            nombre: Chroma(
                collection_name=nombre,
                embedding_function=emb,
                persist_directory=directorio,
                collection_metadata={"hnsw:space": "cosine"},
            )
            for nombre in (config.COLECCION_INTERNOS, config.COLECCION_EXTERNOS)
        }

    def buscar(self, consulta: str, coleccion: str, k: int | None = None,
               umbral: float | None = None) -> list[Fragmento]:
        """Calcula el puntaje de similitud ANTES de inyectar contexto; descarta lo irrelevante."""
        k = k or config.TOP_K
        umbral = self.umbral if umbral is None else umbral
        resultados = self.colecciones[coleccion].similarity_search_with_relevance_scores(consulta, k=k)
        fragmentos = [
            Fragmento(
                contenido=doc.page_content,
                fuente=doc.metadata.get("fuente", "?"),
                seccion=str(doc.metadata.get("seccion", "")),
                tipo_fuente=doc.metadata.get("tipo_fuente", ""),
                version=doc.metadata.get("version", ""),
                score=round(score, 3),
            )
            for doc, score in resultados
            if score >= umbral
        ]
        return sorted(fragmentos, key=lambda f: f.score, reverse=True)


def formatear_contexto(fragmentos: list[Fragmento]) -> str:
    """Delimita cada fragmento con etiquetas para que el LLM distinga fuente y contenido."""
    if not fragmentos:
        return "SIN_RESULTADOS: no se encontró información relevante en la base de conocimiento."
    bloques = []
    for i, f in enumerate(fragmentos, 1):
        bloques.append(
            f'<fragmento id="{i}" fuente="{f.fuente}" seccion="{f.seccion}" tipo="{f.tipo_fuente}" '
            f'score="{f.score}">\n{f.contenido}\n</fragmento>'
        )
    return "\n".join(bloques)
