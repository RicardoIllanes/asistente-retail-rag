"""Agente con tool-calling sobre Gemini: decide qué fuentes consultar, recupera contexto y genera la respuesta."""
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src import config, tools
from src.guardrails import enmascarar_pii
from src.memory import MemoriaConversacional
from src.prompts import FEW_SHOT, SYSTEM_PROMPT


@dataclass
class RespuestaAgente:
    texto: str
    herramientas_usadas: list[str] = field(default_factory=list)
    traza: list[dict] = field(default_factory=list)


def crear_llm():
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=config.LLM_MODEL,
        temperature=config.TEMPERATURE,
        max_output_tokens=config.MAX_OUTPUT_TOKENS,
        google_api_key=config.GOOGLE_API_KEY,
        max_retries=6,  # reintenta ante errores temporales (503 alta demanda, 429 cuota)
    )


class AgenteAtencion:
    def __init__(self, llm=None, memoria: MemoriaConversacional | None = None):
        self.llm = (llm or crear_llm()).bind_tools(tools.HERRAMIENTAS)
        self.memoria = memoria or MemoriaConversacional()
        self.mapa = {t.name: t for t in tools.HERRAMIENTAS}

    def _mensajes_base(self, consulta: str) -> list:
        mensajes = [SystemMessage(SYSTEM_PROMPT)]
        for pregunta, respuesta in FEW_SHOT:
            mensajes += [HumanMessage(pregunta), AIMessage(respuesta)]
        mensajes += self.memoria.como_mensajes()
        hechos = self.memoria.resumen_hechos()
        mensajes.append(HumanMessage(f"{hechos}\n\n{consulta}" if hechos else consulta))
        return mensajes

    def responder(self, consulta_usuario: str) -> RespuestaAgente:
        consulta = enmascarar_pii(consulta_usuario)
        tools.TRAZA.clear()
        mensajes = self._mensajes_base(consulta)
        usadas: list[str] = []
        for _ in range(config.MAX_ITERACIONES_AGENTE):
            ai = self.llm.invoke(mensajes)
            mensajes.append(ai)
            if not getattr(ai, "tool_calls", None):
                break
            for llamada in ai.tool_calls:
                herramienta = self.mapa.get(llamada["name"])
                salida = herramienta.invoke(llamada["args"]) if herramienta else "Herramienta no disponible"
                usadas.append(llamada["name"])
                mensajes.append(ToolMessage(content=salida, tool_call_id=llamada["id"]))
        else:
            ai = AIMessage("No pude completar tu consulta. Te derivo con un ejecutivo humano.")
        texto = ai.content if isinstance(ai.content, str) else "".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in ai.content
        )
        self.memoria.agregar(consulta, texto)
        return RespuestaAgente(texto=texto, herramientas_usadas=usadas, traza=list(tools.TRAZA))
