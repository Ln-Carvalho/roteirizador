# ARCHITECTURE — Roteirizador

> Como o sistema é construído. Módulos pequenos, responsabilidade única, testáveis isoladamente.
> A camada de interface (`app.py`) não contém lógica de negócio — só orquestra os módulos do `core/`.

---

## 1. Estrutura de arquivos proposta

```
roteirizador/
├── app.py                      # Streamlit: wizard de 3 etapas. Só UI + estado + orquestração.
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── models.py               # dataclasses: Ponto, TipoVeiculo, Cenario, Rota, Solucao
│   ├── geocoding.py            # endereço -> (lat, lon)            [Nominatim/geopy]
│   ├── distance.py             # lista de coords -> matriz NxN     [OSRM /table]
│   ├── routing_geometry.py     # sequência de coords -> polilinha  [OSRM /route]
│   ├── solver.py               # Cenario -> Solucao                [VRPSolverEasy]
│   └── mapa.py                 # Solucao + coords -> folium.Map    [Folium]
├── tests/
│   ├── test_solver.py          # regressão contra a instância de Niterói
│   ├── test_distance.py
│   └── test_geocoding.py
└── docs/                       # esta documentação
```

**Princípio:** `app.py` chama `core/`. `core/` nunca importa Streamlit. Isso mantém a lógica
testável sem subir a UI e deixa cada módulo substituível.

## 2. Modelo de dados (`core/models.py`)

Use `@dataclass`. Estas estruturas são o **contrato** que flui entre os módulos e a UI.

```python
@dataclass
class Ponto:
    id: int                 # índice estável; depósitos e clientes compartilham o espaço de ids
    endereco: str
    lat: float | None       # preenchido após geocoding
    lon: float | None
    is_deposito: bool
    demanda: float          # 0 para depósitos

@dataclass
class TipoVeiculo:
    id: int
    nome: str               # rótulo livre ("Moto", "Van")
    capacidade: float
    quantidade: int         # max_number
    custo_por_km: float     # var_cost_dist
    deposito_id: int        # id do Ponto que é o depósito de origem

@dataclass
class Cenario:
    pontos: list[Ponto]
    veiculos: list[TipoVeiculo]
    retornar_ao_deposito: bool   # toggle global

@dataclass
class Rota:
    veiculo_tipo: str
    deposito_id: int
    sequencia_ids: list[int]     # [deposito, c1, c2, ..., (deposito)]
    carga_usada: float
    capacidade: float
    distancia: float

@dataclass
class Solucao:
    rotas: list[Rota]
    custo_total: float
    tempo_solucao: float
    status: str                  # "otimo" | "inviavel" | "erro"
    mensagem: str
```

## 3. Fluxo de dados (ao clicar "Calcular rota")

```
[Etapa 1+2 na UI] Cenario com endereços, demandas, depósitos, tipos de veículo
        │
        │ 1. geocoding.py: para cada Ponto sem lat/lon, geocodifica (Nominatim)
        ▼
Cenario com todos os Pontos georreferenciados
        │
        │ 2. distance.py: monta matriz NxN de distâncias reais (OSRM /table)
        ▼
matriz_dist[N][N]  (em km)
        │
        │ 3. solver.py: constrói o modelo VRPSolverEasy e resolve
        │      - add_depot(id) para cada Ponto com is_deposito
        │      - add_customer(id, demanda) para os demais
        │      - add_vehicle_type(...) para cada TipoVeiculo
        │      - add_link(i, j, distancia) para todos os pares (matriz)
        │      - solve()
        ▼
Solucao (lista de Rota com sequência de ids, carga, distância, custo total)
        │
        │ 4. routing_geometry.py: para cada par consecutivo na rota, pega a polilinha (OSRM /route)
        ▼
geometria de cada rota (lista de (lat,lon) seguindo as ruas)
        │
        │ 5. mapa.py: desenha marcadores + polilinhas coloridas (Folium)
        ▼
folium.Map  ──► renderizado por streamlit-folium na Etapa 3
```

> **Otimização opcional:** OSRM `/route` aceita `overview=full`; uma chamada por rota (passando a
> sequência inteira) já devolve a geometria do trajeto completo daquela rota — prefira isso a uma
> chamada por trecho, para reduzir requisições ao servidor público.

## 4. Contratos entre módulos (assinaturas-alvo)

Mantenha os módulos do `core/` puros e com interface mínima:

```python
# geocoding.py
def geocodificar(endereco: str) -> tuple[float, float] | None
def geocodificar_lote(enderecos: list[str]) -> list[tuple[float, float] | None]

# distance.py
def matriz_distancias(coords: list[tuple[float, float]]) -> list[list[float]]   # km

# routing_geometry.py
def geometria_rota(coords_ordenadas: list[tuple[float, float]]) -> list[tuple[float, float]]

# solver.py
def resolver(cenario: Cenario, matriz_dist: list[list[float]]) -> Solucao

# mapa.py
def desenhar(solucao: Solucao, pontos: list[Ponto],
             geometrias: dict[int, list[tuple[float, float]]]) -> "folium.Map"
```

## 5. Tratamento de erros (comportamento exigido)

| Situação | Onde detectar | Comportamento na UI |
|---|---|---|
| Endereço não geocodificado | `geocoding.py` retorna `None` | Linha destacada em vermelho, "endereço não encontrado"; bloqueia avanço até corrigir |
| Demanda total > capacidade total | validação na Etapa 2 (antes do solver) | Mensagem "frota insuficiente: demanda X > capacidade Y"; botão Calcular desabilitado |
| Nenhum depósito / nenhum cliente | validação na Etapa 1 | Aviso; botão Avançar desabilitado |
| OSRM indisponível / limite atingido | `distance.py` / `routing_geometry.py` | Captura exceção; mensagem "serviço de rotas indisponível, tente novamente"; sem crash |
| Solver retorna inviável | `solver.py` lê `model.status` | `Solucao.status = "inviavel"`; UI mostra explicação em linguagem simples |
| Exceção inesperada do solver | `solver.py` | `Solucao.status = "erro"` + mensagem; UI mostra sem derrubar o app |

Regra geral: **nenhuma exceção não tratada deve quebrar o Streamlit**. Toda falha externa
(geocoding, OSRM, solver) vira uma mensagem amigável na tela.

## 6. Estado da aplicação (`st.session_state`)

Chaves mínimas:

- `etapa` (int 1–3) — etapa atual do wizard.
- `pontos` (list[Ponto]) — tabela de endereços da Etapa 1.
- `veiculos` (list[TipoVeiculo]) — frota da Etapa 2.
- `retornar_ao_deposito` (bool).
- `solucao` (Solucao | None) — resultado da Etapa 3 (cache para não recalcular ao re-renderizar).

Botões "Avançar"/"Voltar" mudam `etapa`. "Calcular rota" dispara o fluxo da §3 e guarda `solucao`.

## 7. Caching e desempenho

- Use `@st.cache_data` em `geocodificar_lote` e `matriz_distancias` (entradas idênticas → não
  refaz chamada externa). Isso respeita os limites dos servidores públicos e acelera recálculos.
- O solver **não** deve ser cacheado de forma a esconder mudanças de parâmetro; recalcule quando o
  cenário muda.
- Respeite o rate limit do Nominatim (≥ 1 s entre chamadas) — ver `TECH_STACK.md`.
