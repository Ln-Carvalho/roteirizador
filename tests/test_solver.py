from pathlib import Path
import pytest
import pandas as pd
from core.models import Ponto, TipoVeiculo, Cenario
from core.solver import resolver

MATRIX_PATH = Path(__file__).parent.parent.parent / "Trabalho_final" / "dist_matrix_km.xlsx"

DEMANDAS = {
    0: 0, 1: 120, 2: 80, 3: 150, 4: 200, 5: 90, 6: 110,
    7: 130, 8: 70, 9: 100, 10: 60, 11: 140, 12: 50, 13: 160,
    14: 180, 15: 75, 16: 95, 17: 85, 18: 65, 19: 55, 20: 125,
}

# Established 2026-06-07: VRPSolverEasy direct call, 1 depot/1 type, closed route, cost_per_km=1.0
BASELINE_COST = 123.198


def _load_matrix() -> list[list[float]]:
    df = pd.read_excel(MATRIX_PATH, index_col=0)
    return df.values.tolist()


def _pontos_ref(n: int) -> list[Ponto]:
    return [
        Ponto(
            id=i, endereco="", lat=None, lon=None,
            is_deposito=(i == 0), demanda=DEMANDAS[i],
        )
        for i in range(n)
    ]


def test_regressao_solver_1deposito_1tipo():
    """
    With the Niterói reference matrix and same config as baseline,
    core/solver.resolver() must reproduce cost 123.198 km (±0.01).
    This proves core/solver.py does not distort VRPSolverEasy math.
    """
    matriz = _load_matrix()
    n = len(matriz)
    pontos = _pontos_ref(n)
    veiculo = TipoVeiculo(
        id=1, nome="Van", capacidade=500, quantidade=10,
        custo_por_km=1.0, deposito_id=0,
    )
    cenario = Cenario(pontos=pontos, veiculos=[veiculo], retornar_ao_deposito=True)

    sol = resolver(cenario, matriz)

    assert sol.status == "otimo", f"Status inesperado: {sol.status} — {sol.mensagem}"
    assert abs(sol.custo_total - BASELINE_COST) < 0.01, (
        f"Custo {sol.custo_total:.3f} difere do baseline {BASELINE_COST}"
    )
    for rota in sol.rotas:
        assert rota.carga_usada <= rota.capacidade + 0.001, (
            f"Rota excede capacidade: {rota.carga_usada} > {rota.capacidade}"
        )
    clientes_atendidos = {
        pid for rota in sol.rotas for pid in rota.sequencia_ids if pid != 0
    }
    assert clientes_atendidos == set(range(1, n)), "Nem todos os clientes foram atendidos"


def test_solver_multi_deposito_2tipos():
    """
    2 depots (ids 0,1) + 2 vehicle types → all 3 clients served, no capacity violation.
    Uses a fixed 5x5 matrix (no network dependency).
    """
    dist = [
        [0.0,  2.0, 5.0,  8.0, 10.0],  # 0 (dep1)
        [2.0,  0.0, 3.0,  6.0,  8.0],  # 1 (dep2)
        [5.0,  3.0, 0.0,  4.0,  6.0],  # 2 (c1)
        [8.0,  6.0, 4.0,  0.0,  3.0],  # 3 (c2)
        [10.0, 8.0, 6.0,  3.0,  0.0],  # 4 (c3)
    ]
    pontos = [
        Ponto(id=0, endereco="Dep1", lat=None, lon=None, is_deposito=True,  demanda=0),
        Ponto(id=1, endereco="Dep2", lat=None, lon=None, is_deposito=True,  demanda=0),
        Ponto(id=2, endereco="C1",   lat=None, lon=None, is_deposito=False, demanda=50),
        Ponto(id=3, endereco="C2",   lat=None, lon=None, is_deposito=False, demanda=50),
        Ponto(id=4, endereco="C3",   lat=None, lon=None, is_deposito=False, demanda=50),
    ]
    veiculos = [
        TipoVeiculo(id=1, nome="TipoA", capacidade=200, quantidade=2,
                    custo_por_km=1.0, deposito_id=0),
        TipoVeiculo(id=2, nome="TipoB", capacidade=200, quantidade=2,
                    custo_por_km=1.0, deposito_id=1),
    ]
    cenario = Cenario(pontos=pontos, veiculos=veiculos, retornar_ao_deposito=True)

    sol = resolver(cenario, dist)

    assert sol.status == "otimo", f"Multi-depot falhou: {sol.status} — {sol.mensagem}"
    for rota in sol.rotas:
        assert rota.carga_usada <= rota.capacidade + 0.001
    deposito_ids = {0, 1}
    clientes_atendidos = {
        pid for rota in sol.rotas for pid in rota.sequencia_ids if pid not in deposito_ids
    }
    assert clientes_atendidos == {2, 3, 4}, f"Clientes faltando: {clientes_atendidos}"
