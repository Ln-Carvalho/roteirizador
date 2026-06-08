from core.routing_geometry import geometria_rota

COORDS_SEQUENCIA = [
    (-22.908, -43.131),  # depot
    (-22.892, -43.108),  # point 1
    (-22.897, -43.114),  # point 2
    (-22.908, -43.131),  # depot return
]


def test_geometria_rota_retorna_lista_coords():
    poly = geometria_rota(COORDS_SEQUENCIA)
    assert isinstance(poly, list)
    assert len(poly) >= 2
    for pt in poly:
        assert isinstance(pt, tuple)
        assert len(pt) == 2
        lat, lon = pt
        # Bounding box: Sul do Brasil (inclui RJ)
        assert -35.0 < lat < -5.0
        assert -55.0 < lon < -30.0


def test_geometria_rota_unico_ponto_retorna_vazio():
    poly = geometria_rota([(-22.908, -43.131)])
    assert poly == []


def test_geometria_rota_lista_vazia_retorna_vazio():
    poly = geometria_rota([])
    assert poly == []
