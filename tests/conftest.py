import pytest

from src import tools
from src.ingest import indexar
from src.retriever import Recuperador


@pytest.fixture(scope="session")
def recuperador(tmp_path_factory):
    """Índice temporal con embeddings locales: las pruebas no consumen API ni requieren conexión."""
    destino = tmp_path_factory.mktemp("vs")
    indexar("local", destino)
    rec = Recuperador("local", destino)
    tools.set_recuperador(rec)
    return rec
