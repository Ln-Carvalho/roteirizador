from dataclasses import dataclass


@dataclass
class Ponto:
    id: int
    endereco: str
    lat: float | None
    lon: float | None
    is_deposito: bool
    demanda: float


@dataclass
class TipoVeiculo:
    id: int
    nome: str
    capacidade: float
    quantidade: int
    custo_por_km: float
    deposito_id: int


@dataclass
class Cenario:
    pontos: list[Ponto]
    veiculos: list[TipoVeiculo]
    retornar_ao_deposito: bool
    permitir_multiplas_viagens: bool = False


@dataclass
class Rota:
    veiculo_tipo: str
    deposito_id: int
    sequencia_ids: list[int]
    carga_usada: float
    capacidade: float
    distancia: float


@dataclass
class Solucao:
    rotas: list[Rota]
    custo_total: float
    tempo_solucao: float
    status: str        # "otimo" | "inviavel" | "erro"
    mensagem: str
