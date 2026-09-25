"""Prueba del bucle del agente con un LLM simulado (sin API): verifica tool-calling, trazabilidad y memoria."""
from langchain_core.messages import AIMessage

from src.agent import AgenteAtencion


class LLMSimulado:
    """Primera llamada: pide consultar el pedido. Segunda: responde con el resultado."""

    def __init__(self):
        self.llamadas = 0
        self.ultimo_prompt = None

    def bind_tools(self, _):
        return self

    def invoke(self, mensajes):
        self.llamadas += 1
        self.ultimo_prompt = mensajes
        if self.llamadas == 1:
            return AIMessage("", tool_calls=[{"name": "consultar_pedido", "args": {"codigo_pedido": "TH-10260"}, "id": "1"}])
        return AIMessage("Tu pedido TH-10260 tiene una incidencia; te derivo a un ejecutivo.\n\nFuentes: pedidos.csv §TH-10260")


def test_agente_usa_herramienta_y_registra_traza():
    llm = LLMSimulado()
    agente = AgenteAtencion(llm=llm)
    r = agente.responder("¿Qué pasa con mi pedido TH-10260? mi correo es juan@mail.cl")
    assert r.herramientas_usadas == ["consultar_pedido"]
    assert r.traza[0]["fuente"] == "pedidos.csv"
    assert "Fuentes:" in r.texto
    # el PII nunca llega al LLM
    assert all("juan@mail.cl" not in str(m.content) for m in llm.ultimo_prompt)
    assert agente.memoria.hechos["ultimo_pedido"] == "TH-10260"
