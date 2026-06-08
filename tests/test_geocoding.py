from core.geocoding import geocodificar, geocodificar_lote


def test_geocodificar_endereco_valido():
    resultado = geocodificar("Rua da Conceição, 29, Centro, Niterói - RJ, Brasil")
    assert resultado is not None
    lat, lon = resultado
    # Bounding box de Niterói (aprox.)
    assert -22.99 < lat < -22.85
    assert -43.18 < lon < -43.05


def test_geocodificar_endereco_invalido():
    resultado = geocodificar("Rua Inexistente do Lugar Nenhum 99999, ZZ")
    assert resultado is None


def test_geocodificar_lote_misturado():
    enderecos = [
        "Rua da Conceição, 29, Niterói - RJ, Brasil",
        "Endereco Completamente Falso XYZ 99999999",
    ]
    resultados = geocodificar_lote(enderecos)
    assert len(resultados) == 2
    assert resultados[0] is not None
    assert resultados[1] is None
