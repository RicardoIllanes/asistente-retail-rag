"""Herramientas del agente. Cada una devuelve texto delimitado con metadatos de fuente (trazabilidad)."""
import csv

from langchain_core.tools import tool

from src import config
from src.retriever import Recuperador, formatear_contexto

_recuperador: Recuperador | None = None
# Registro de las fuentes usadas en el turno actual (para trazabilidad y evaluación)
TRAZA: list[dict] = []


def get_recuperador() -> Recuperador:
    global _recuperador
    if _recuperador is None:
        _recuperador = Recuperador()
    return _recuperador


def set_recuperador(recuperador: Recuperador) -> None:
    global _recuperador
    _recuperador = recuperador


def _buscar(consulta: str, coleccion: str, filtro_fuente: str | None = None) -> str:
    fragmentos = get_recuperador().buscar(consulta, coleccion)
    if filtro_fuente == "catalogo":
        fragmentos = [f for f in fragmentos if f.fuente == "catalogo_productos.csv"]
    elif filtro_fuente == "politicas":
        fragmentos = [f for f in fragmentos if f.fuente != "catalogo_productos.csv"]
    for f in fragmentos:
        TRAZA.append({"herramienta": coleccion, "fuente": f.fuente, "seccion": f.seccion, "score": f.score,
                      "contenido": f.contenido})
    return formatear_contexto(fragmentos)


@tool
def buscar_politicas_internas(consulta: str) -> str:
    """Busca en las políticas internas de TecnoHogar: garantías, devoluciones, despachos, pagos, boletas, tienda y FAQ."""
    return _buscar(consulta, config.COLECCION_INTERNOS, "politicas")


@tool
def buscar_catalogo(consulta: str) -> str:
    """Busca productos del catálogo de TecnoHogar: precio, stock, marca y meses de garantía del fabricante."""
    return _buscar(consulta, config.COLECCION_INTERNOS, "catalogo")


@tool
def buscar_normativa_consumidor(consulta: str) -> str:
    """Busca en la Ley 19.496 de Protección al Consumidor y guías del SERNAC (fuente externa oficial)."""
    return _buscar(consulta, config.COLECCION_EXTERNOS)


@tool
def consultar_pedido(codigo_pedido: str) -> str:
    """Consulta el estado de un pedido en el sistema de pedidos. El código tiene formato TH-XXXXX (ej.: TH-10245)."""
    codigo = codigo_pedido.strip().upper()
    with (config.INTERNOS_DIR / "pedidos.csv").open(encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila["id_pedido"] == codigo:
                TRAZA.append({"herramienta": "pedidos", "fuente": "pedidos.csv", "seccion": codigo, "score": 1.0,
                              "contenido": str(fila)})
                seguimiento = f"{fila['courier']} {fila['n_seguimiento']}" if fila["courier"] else "aún no asignado"
                return (
                    f'<pedido fuente="pedidos.csv" id="{codigo}">\n'
                    f"Estado: {fila['estado']} | Fecha de compra: {fila['fecha_compra']} | Región: {fila['region']} | "
                    f"Producto: {fila['sku']} | Seguimiento: {seguimiento} | "
                    f"Entrega estimada: {fila['fecha_estimada_entrega']}\n</pedido>"
                )
    return f"SIN_RESULTADOS: no existe el pedido {codigo}. Pide al cliente verificar el código."


HERRAMIENTAS = [buscar_politicas_internas, buscar_catalogo, buscar_normativa_consumidor, consultar_pedido]
