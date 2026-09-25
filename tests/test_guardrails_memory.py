from src.guardrails import enmascarar_pii, extraer_codigo_pedido
from src.memory import MemoriaConversacional


def test_enmascara_datos_personales():
    texto = "Soy 12.345.678-9, mi correo es ana@mail.cl, fono +56 9 8765 4321, tarjeta 4111 1111 1111 1111"
    salida = enmascarar_pii(texto)
    for dato in ("12.345.678-9", "ana@mail.cl", "8765", "4111"):
        assert dato not in salida
    assert "[RUT]" in salida and "[EMAIL]" in salida and "[TARJETA]" in salida


def test_codigo_pedido_no_se_enmascara():
    assert enmascarar_pii("mi pedido TH-10245") == "mi pedido TH-10245"
    assert extraer_codigo_pedido("hola, el th-10231 no llega") == "TH-10231"


def test_memoria_ventana_deslizante_y_hechos():
    m = MemoriaConversacional(max_turnos=2)
    m.agregar("mi pedido es TH-10252", "ok")
    m.agregar("¿cuándo llega?", "el 30-09")
    m.agregar("gracias", "de nada")
    assert len(m.turnos) == 2 and len(m.como_mensajes()) == 4
    assert m.hechos["ultimo_pedido"] == "TH-10252"  # se conserva aunque el turno salió de la ventana
