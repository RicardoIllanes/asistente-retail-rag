"""Fábrica de modelos de embeddings.

- gemini: GoogleGenerativeAIEmbeddings (semántico, requiere GOOGLE_API_KEY).
- local : embedding léxico por hashing (bolsa de palabras normalizada). No entiende sinónimos,
          pero permite ejecutar pruebas y evaluación sin costo ni conexión.
"""
import hashlib
import math
import re
import unicodedata

from langchain_core.embeddings import Embeddings

from src import config

STOPWORDS = set(
    "el la los las un una unos unas de del al a en y o u que se por para con sin su sus es son "
    "mi mis me lo le les como cual cuales cuando donde puedo puede tengo tiene hay mas muy ya "
    "si no este esta estos estas ese esa eso".split()
)


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def tokenizar(texto: str) -> list[str]:
    palabras = re.findall(r"[a-z0-9]+", normalizar(texto))
    # stemming mínimo: recorta plurales simples
    return [p[:-1] if len(p) > 4 and p.endswith("s") else p for p in palabras if p not in STOPWORDS]


class HashingEmbeddings(Embeddings):
    """Embedding léxico determinista (vector de 16384 dimensiones, norma L2 = 1)."""

    def __init__(self, dim: int = 16384):
        self.dim = dim

    def _embed(self, texto: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in tokenizar(texto):
            idx = int(hashlib.sha1(tok.encode()).hexdigest(), 16) % self.dim
            vec[idx] += 1.0
        vec = [math.log1p(v) for v in vec]  # tf sublineal: reduce el peso de palabras repetidas
        norma = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norma for v in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def get_embeddings(provider: str | None = None) -> Embeddings:
    provider = provider or config.EMBEDDINGS_PROVIDER
    if provider == "local":
        return HashingEmbeddings()
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(model=config.EMBEDDING_MODEL, google_api_key=config.GOOGLE_API_KEY)
