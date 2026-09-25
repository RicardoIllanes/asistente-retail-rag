from src import config
from src.ingest import cargar_catalogo, cargar_markdown, construir_documentos


def test_chunks_respetan_tamano_y_tienen_metadatos():
    docs = cargar_markdown(config.INTERNOS_DIR / "politica_garantias.md", "interna")
    assert len(docs) > 3
    for d in docs:
        # tamaño del chunk + encabezado de contexto antepuesto
        assert len(d.page_content) <= config.CHUNK_SIZE + 150
        for clave in ("fuente", "seccion", "tipo_fuente", "version"):
            assert d.metadata[clave] != "" or clave == "version"
        assert d.metadata["fuente"] == "politica_garantias.md"


def test_catalogo_un_documento_por_producto():
    docs = cargar_catalogo(config.INTERNOS_DIR / "catalogo_productos.csv")
    assert len(docs) == 8
    lavadora = next(d for d in docs if d.metadata["seccion"] == "TH-LV12")
    assert "SIN STOCK" in lavadora.page_content


def test_separacion_fuentes_internas_y_externas():
    internos, externos = construir_documentos()
    assert all(d.metadata["tipo_fuente"] == "interna" for d in internos)
    assert all(d.metadata["tipo_fuente"] == "externa" for d in externos)
    assert {d.metadata["fuente"] for d in externos} == {"ley_19496_extracto.md", "sernac_guia_compras_online.md"}
