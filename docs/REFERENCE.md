# REFERENCE — API do VRPSolverEasy e código a reaproveitar

> Referência concreta extraída do projeto original (`../Trabalho_final/notebook_tf.ipynb`), que já
> resolve um CVRP real com o VRPSolverEasy. Use isto para não re-derivar a API do zero.

---

## 1. API do VRPSolverEasy (como já é usada hoje)

```python
import VRPSolverEasy as vre

model = vre.Model()

# --- Tipo de veículo ---
# start_point_id / end_point_id referenciam ids de depósito.
# end_point_id = start_point_id  -> veículo VOLTA ao depósito (rota fechada)
# end_point_id = -1              -> rota ABERTA (não volta)
model.add_vehicle_type(
    id=1,                       # id único do tipo
    start_point_id=0,           # depósito de origem
    end_point_id=0,             # depósito de retorno (ou -1 p/ aberta)
    capacity=500,
    max_number=10,              # quantidade de veículos desse tipo
    var_cost_dist=1.0,          # custo por unidade de distância -> objetivo
)

# --- Depósito ---
model.add_depot(id=0)           # aceita também service_time, tw_begin, tw_end (não usados no MVP)

# --- Clientes ---
for i in range(1, N):
    model.add_customer(id=i, demand=demandas[i])

# --- Links (arcos) — usar a matriz de distâncias ---
# is_directed=True permite matriz assimétrica (ida != volta), que é o caso do OSRM/Google.
for i in range(N):
    for j in range(N):
        if i != j:
            model.add_link(
                start_point_id=i,
                end_point_id=j,
                distance=round(float(matriz[i][j]), 3),
                is_directed=True,
            )

# --- Resolver ---
model.set_parameters(solver_name="CLP")
model.solve()

print(model.status, model.message)

# --- Ler a solução ---
sol = model.solution
if sol.is_defined:
    custo_total = sol.value                  # custo da solução
    for route in sol.routes:
        ids   = route.point_ids              # ex.: [0, 7, 6, 9, 2, 0]  (inclui depósito)
        carga = route.cap_consumption        # carga usada na rota
    # estatísticas:
    model.statistics.solution_time
    model.statistics.best_lb
    model.statistics.nb_branch_and_bound_nodes
```

### Notas de modelagem importantes

- **Espaço de ids único:** depósitos e clientes compartilham o mesmo espaço de `id`. Defina os ids
  dos depósitos primeiro (ex.: 0, 1, ...) e os clientes em seguida, de forma estável. A matriz de
  distâncias deve cobrir **todos** os pontos (depósitos + clientes) na mesma indexação.
- **Multi-depósito + frota heterogênea (o que o MVP exige):** crie **um `add_depot` por depósito**
  e **um `add_vehicle_type` por tipo de veículo**, com `start_point_id`/`end_point_id` apontando
  para o depósito daquele tipo. Tipos diferentes podem apontar para depósitos diferentes.
- **Toggle "voltar ao depósito" (global):**
  - ligado  → para cada tipo, `end_point_id = start_point_id`;
  - desligado → para cada tipo, `end_point_id = -1`.
- **`var_cost_dist`** é o `custo_por_km` da UI. O objetivo minimizado é a soma de
  `distância × var_cost_dist` (+ custos fixos, se usados) sobre todas as rotas.
- **Depósitos têm demanda 0.**
- O notebook usa `var_cost_dist = CUSTO_POR_KM/10` em um experimento — no app, use o valor do
  usuário diretamente (sem dividir).

## 2. Código existente a reaproveitar (`../Trabalho_final/`)

| Arquivo | Conteúdo | Como usar no app |
|---|---|---|
| `notebook_tf.ipynb` | Construção completa do modelo VRPSolverEasy + leitura da solução + geração de URLs do mapa | **Fonte primária** para `core/solver.py`. Adapte de single-depot/homogêneo para multi-depot/heterogêneo conforme §1. |
| `01_geocoding.py` | Geocoding via Google | Lógica de fluxo aproveitável; **troque o provedor** para Nominatim (ver TECH_STACK §2). |
| `02_dist_matrix.py` | Matriz de distância via Google, em blocos | Estrutura de montagem da matriz aproveitável; **troque o provedor** para OSRM `/table`. |
| `coordsf.xlsx` | Coordenadas reais de ~21 pontos (Niterói/Rio) | Dados de teste para `tests/`. |
| `dist_matrix_km.xlsx` | Matriz de distância NxN em km | **Fixture de regressão** do solver (ver §3). |
| `criar_enderecos.py` | Lista de endereços de exemplo | Dados de exemplo para pré-popular a Etapa 1 numa demo. |

> O Google Maps usado nos scripts originais **não vai para o app** (decisão D2). Reaproveite a
> *estrutura*, não o provedor. A chave de API que aparece hardcoded nesses scripts **não deve ser
> copiada** para o novo código.

## 3. Teste de regressão do solver

`tests/test_solver.py` deve garantir que a refatoração não mudou a matemática:

1. Carregue `../Trabalho_final/dist_matrix_km.xlsx` (matriz NxN) e as demandas do notebook.
2. Monte um `Cenario` com **1 depósito (ponto 0)** + **1 tipo de veículo** equivalente ao do
   notebook (capacidade 500, retorno ao depósito conforme o notebook).
3. Rode `core/solver.resolver(...)`.
4. **Asserção:** o `custo_total` deve bater com o que o notebook produz para a mesma configuração
   (rode o notebook uma vez para registrar o valor esperado como baseline).

Isso prova que `core/solver.py` é fiel ao modelo original antes de exercitar multi-depósito.

## 4. Exemplo de cenário multi-depósito (para teste manual / demo)

Use endereços reais de Niterói e Rio (já presentes em `criar_enderecos.py`) e monte algo como:

- **Depósitos:** ponto em Niterói (D1) + ponto no Centro do Rio (D2).
- **Clientes:** farmácias restantes, com demandas variadas.
- **Frota:** 2 "Vans" (cap 500) em D1, 1 "Van" (cap 500) em D2, 2 "Motos" (cap 200) em D1.
- Espere ver rotas saindo de **ambos** os depósitos no mapa, com cores distintas.
