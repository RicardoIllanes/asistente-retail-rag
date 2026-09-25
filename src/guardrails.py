"""Privacidad: enmascara datos personales antes de enviarlos al LLM o a los registros (logs)."""
import re

PATRONES = [
    ("TARJETA", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    ("RUT", re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b")),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")),
    ("TELEFONO", re.compile(r"(?:\+?56\s?)?\b9\s?\d{4}\s?\d{4}\b")),
]


def enmascarar_pii(texto: str) -> str:
    for etiqueta, patron in PATRONES:
        texto = patron.sub(f"[{etiqueta}]", texto)
    return texto


CODIGO_PEDIDO = re.compile(r"\bTH-\d{5}\b", re.IGNORECASE)


def extraer_codigo_pedido(texto: str) -> str | None:
    m = CODIGO_PEDIDO.search(texto)
    return m.group(0).upper() if m else None
