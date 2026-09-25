from src import tools


def test_consultar_pedido_existente():
    salida = tools.consultar_pedido.invoke({"codigo_pedido": "th-10245"})
    assert "DESPACHADO" in salida and "Starken ST55410" in salida


def test_consultar_pedido_inexistente():
    assert tools.consultar_pedido.invoke({"codigo_pedido": "TH-99999"}).startswith("SIN_RESULTADOS")


def test_buscar_catalogo_solo_devuelve_productos(recuperador):
    salida = tools.buscar_catalogo.invoke({"consulta": "precio refrigerador no frost 340 litros"})
    assert "catalogo_productos.csv" in salida and "politica_" not in salida
    assert "459.990" in salida


def test_traza_registra_fuentes(recuperador):
    tools.TRAZA.clear()
    tools.buscar_normativa_consumidor.invoke({"consulta": "garantía legal 6 meses"})
    assert tools.TRAZA and all(t["fuente"].endswith(".md") for t in tools.TRAZA)
