"""Control de contexto conversacional: ventana deslizante de los últimos N turnos.

Evita superar la ventana de contexto del modelo y reduce el consumo de tokens, conservando
los datos clave (por ejemplo, el último código de pedido mencionado) como 'hechos' persistentes.
"""
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from src import config
from src.guardrails import extraer_codigo_pedido


class MemoriaConversacional:
    def __init__(self, max_turnos: int | None = None):
        self.max_turnos = max_turnos or config.MAX_TURNOS_MEMORIA
        self.turnos: list[tuple[str, str]] = []
        self.hechos: dict[str, str] = {}

    def agregar(self, usuario: str, asistente: str) -> None:
        self.turnos.append((usuario, asistente))
        self.turnos = self.turnos[-self.max_turnos:]
        codigo = extraer_codigo_pedido(usuario)
        if codigo:
            self.hechos["ultimo_pedido"] = codigo

    def como_mensajes(self) -> list[BaseMessage]:
        mensajes: list[BaseMessage] = []
        for u, a in self.turnos:
            mensajes += [HumanMessage(u), AIMessage(a)]
        return mensajes

    def resumen_hechos(self) -> str:
        if not self.hechos:
            return ""
        return "Datos recordados de la conversación: " + ", ".join(f"{k}={v}" for k, v in self.hechos.items())

    def limpiar(self) -> None:
        self.turnos.clear()
        self.hechos.clear()
