import pytest
from core.distance import matriz_distancias

COORDS_NITEROI = [
    (-22.908, -43.131),   # Rua Dr Paulo César
    (-22.892, -43.108),   # Icaraí area
    (-22.897, -43.114),   # Centro Niterói
]


def test_matriz_dimensoes():
    matriz = matriz_distancias(COORDS_NITEROI)
    n = len(COORDS_NITEROI)
    assert len(matriz) == n
    for linha in matriz:
        assert len(linha) == n


def test_diagonal_zero():
    matriz = matriz_distancias(COORDS_NITEROI)
    for i in range(len(COORDS_NITEROI)):
        assert matriz[i][i] == pytest.approx(0.0, abs=0.01)


def test_valores_positivos_fora_diagonal():
    matriz = matriz_distancias(COORDS_NITEROI)
    for i in range(len(COORDS_NITEROI)):
        for j in range(len(COORDS_NITEROI)):
            if i != j:
                assert matriz[i][j] > 0


def test_ordem_grandeza_km():
    """Pontos em Niterói devem estar a < 20 km entre si."""
    matriz = matriz_distancias(COORDS_NITEROI)
    for i in range(len(COORDS_NITEROI)):
        for j in range(len(COORDS_NITEROI)):
            assert matriz[i][j] < 20.0
