"""Ingesta: carga documentos internos y externos, los fragmenta (chunking) y los indexa en Chroma.

Uso:
    python -m src.ingest                 # indexa data/internos y data/externos
    python -m src.ingest --provider local
"""
import argparse
import csv
import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from src import config
from src.embeddings import get_embeddings


def _leer_version(texto: str) -> str:
    """Extrae la línea de versión/vigencia (segunda línea) para trazabilidad."""
    lineas = [l for l in texto.splitlines() if l.strip()]
    return lineas[1].strip() if len(lineas) > 1 else ""


def cargar_markdown(ruta: Path, tipo_fuente: str) -> list[Document]:
    """Divide primero por encabezados (## sección) y luego por tamaño con solapamiento."""
    texto = ruta.read_text(encoding="utf-8")
    titulo = texto.splitlines()[0].lstrip("# ").strip()
    version = _leer_version(texto)
    por_seccion = MarkdownHeaderTextSplitter(headers_to_split_on=[("##", "seccion")]).split_text(texto)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
    )
    docs = []
    for sec in por_seccion:
        seccion = sec.metadata.get("seccion")
        if not seccion:
            continue  # preámbulo (título y versión): ya se guarda como metadato
        for i, trozo in enumerate(splitter.split_text(sec.page_content)):
            docs.append(
                Document(
                    # El encabezado se antepone al chunk para no perder contexto semántico
                    page_content=f"[{titulo} — {seccion}]\n{trozo}",
                    metadata={
                        "fuente": ruta.name,
                        "titulo": titulo,
                        "seccion": seccion,
                        "tipo_fuente": tipo_fuente,
                        "version": version,
                        "chunk": i,
                    },
                )
            )
    return docs


def cargar_catalogo(ruta: Path) -> list[Document]:
    """Cada producto del catálogo se convierte en un documento autocontenido (1 fila = 1 chunk)."""
    docs = []
    with ruta.open(encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            stock = "disponible" if int(fila["stock"]) > 0 else "SIN STOCK"
            contenido = (
                f"[Catálogo — {fila['nombre']}]\nSKU {fila['sku']} | Marca {fila['marca']} | "
                f"Categoría {fila['categoria']} | Precio ${int(fila['precio_clp']):,} CLP | Stock: {stock} "
                f"({fila['stock']} unidades) | Garantía del fabricante: {fila['garantia_fabricante_meses']} meses.\n"
                f"{fila['descripcion']}"
            ).replace(",", ".")
            docs.append(
                Document(
                    page_content=contenido,
                    metadata={
                        "fuente": ruta.name,
                        "titulo": "Catálogo de productos",
                        "seccion": fila["sku"],
                        "tipo_fuente": "interna",
                        "version": "",
                        "chunk": 0,
                    },
                )
            )
    return docs


def construir_documentos() -> tuple[list[Document], list[Document]]:
    internos = []
    for ruta in sorted(config.INTERNOS_DIR.glob("*.md")):
        internos += cargar_markdown(ruta, "interna")
    internos += cargar_catalogo(config.INTERNOS_DIR / "catalogo_productos.csv")
    externos = []
    for ruta in sorted(config.EXTERNOS_DIR.glob("*.md")):
        externos += cargar_markdown(ruta, "externa")
    return internos, externos


def indexar(provider: str | None = None, destino: Path | None = None) -> dict:
    destino = destino or config.VECTOR_DIR
    if destino.exists():
        shutil.rmtree(destino)  # reindexación completa: evita chunks duplicados u obsoletos
    emb = get_embeddings(provider)
    internos, externos = construir_documentos()
    for nombre, docs in [(config.COLECCION_INTERNOS, internos), (config.COLECCION_EXTERNOS, externos)]:
        Chroma.from_documents(
            docs,
            emb,
            collection_name=nombre,
            persist_directory=str(destino),
            collection_metadata={"hnsw:space": "cosine"},
        )
    return {"internos": len(internos), "externos": len(externos)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indexa la base de conocimiento en Chroma")
    parser.add_argument("--provider", choices=["gemini", "local"], default=None)
    args = parser.parse_args()
    resumen = indexar(args.provider)
    print(f"Indexación completa: {resumen['internos']} chunks internos, {resumen['externos']} chunks externos")
