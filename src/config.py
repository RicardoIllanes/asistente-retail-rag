"""Configuración central del asistente. Los valores se leen desde variables de entorno (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INTERNOS_DIR = DATA_DIR / "internos"
EXTERNOS_DIR = DATA_DIR / "externos"
VECTOR_DIR = BASE_DIR / os.getenv("VECTOR_DIR", "vectorstore")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.8-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
# "gemini" usa embeddings de Google; "local" usa un embedding léxico sin costo (útil para pruebas)
EMBEDDINGS_PROVIDER = os.getenv("EMBEDDINGS_PROVIDER", "gemini")

# Parámetros del LLM: temperatura baja = respuestas más deterministas y menos alucinaciones
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "800"))

# Parámetros de chunking y recuperación
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "700"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
TOP_K = int(os.getenv("TOP_K", "4"))
# Umbral de relevancia (0-1). Fragmentos bajo este puntaje no se inyectan en el prompt.
# Depende del modelo de embeddings: calibrar con `python -m eval.evaluate --umbral X`.
_UMBRAL_POR_DEFECTO = {"gemini": "0.55", "local": "0.12"}
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", _UMBRAL_POR_DEFECTO.get(EMBEDDINGS_PROVIDER, "0.5")))

# Control de contexto conversacional
MAX_TURNOS_MEMORIA = int(os.getenv("MAX_TURNOS_MEMORIA", "6"))
MAX_ITERACIONES_AGENTE = int(os.getenv("MAX_ITERACIONES_AGENTE", "4"))

COLECCION_INTERNOS = "internos"
COLECCION_EXTERNOS = "externos"
