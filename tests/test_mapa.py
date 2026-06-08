import folium
from core.models import Ponto, Rota, Solucao
from core.mapa import desenhar


def _fixture_sol():
    pontos = [
        Ponto(id=0, endereco="Dep", lat=-22.908, lon=-43.131, is_deposito=True,  demanda=0),
        Ponto(id=1, endereco="C1",  lat=-22.892, lon=-43.108, is_deposito=False, demanda=100),
        Ponto(id=2, endereco="C2",  lat=-22.897, lon=-43.114, is_deposito=False, demanda=80),
    ]
    rota = Rota(
        veiculo_tipo="Van", deposito_id=0,
        sequencia_ids=[0, 1, 2, 0],
        carga_usada=180, capacidade=500, distancia=5.0,
    )
    sol = Solucao(rotas=[rota], custo_total=5.0, tempo_solucao=0.1,
                  status="otimo", mensagem="ok")
    geometrias = {
        0: [(-22.908, -43.131), (-22.892, -43.108), (-22.897, -43.114), (-22.908, -43.131)]
    }
    return sol, pontos, geometrias


def test_desenhar_retorna_folium_map():
    sol, pontos, geometrias = _fixture_sol()
    m = desenhar(sol, pontos, geometrias)
    assert isinstance(m, folium.Map)


def test_desenhar_solucao_inviavel_nao_crasha():
    sol_vazia = Solucao(
        rotas=[], custo_total=0.0, tempo_solucao=0.0,
        status="inviavel", mensagem="sem solucao",
    )
    pontos = [Ponto(id=0, endereco="Dep", lat=-22.908, lon=-43.131,
                    is_deposito=True, demanda=0)]
    m = desenhar(sol_vazia, pontos, {})
    assert isinstance(m, folium.Map)
