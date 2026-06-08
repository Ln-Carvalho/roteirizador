from core.models import Ponto, TipoVeiculo, Cenario, Rota, Solucao


def test_cenario_construivel():
    pontos = [
        Ponto(id=0, endereco="Rua A, 1", lat=-22.9, lon=-43.1, is_deposito=True, demanda=0),
        Ponto(id=1, endereco="Rua B, 2", lat=-22.95, lon=-43.15, is_deposito=False, demanda=100),
    ]
    veiculo = TipoVeiculo(
        id=1, nome="Van", capacidade=500, quantidade=2, custo_por_km=1.0, deposito_id=0
    )
    cenario = Cenario(pontos=pontos, veiculos=[veiculo], retornar_ao_deposito=True)

    assert cenario.pontos[0].is_deposito is True
    assert cenario.pontos[1].demanda == 100
    assert cenario.veiculos[0].capacidade == 500
    assert cenario.retornar_ao_deposito is True


def test_solucao_status_padrao():
    sol = Solucao(rotas=[], custo_total=0.0, tempo_solucao=0.0, status="inviavel", mensagem="")
    assert sol.status == "inviavel"
    assert sol.rotas == []
