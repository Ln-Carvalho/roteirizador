# Roteirizador CVRP — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Streamlit web app that takes VRP inputs (addresses, fleet, depots), solves with VRPSolverEasy, and displays routes on a real-streets Folium map — zero API cost, 100% Python.

**Architecture:** Three-step Streamlit wizard (Addresses → Fleet → Results); `core/` modules are pure Python with no Streamlit dependency, each with one responsibility; `app.py` only orchestrates `core/` and manages `st.session_state`. External services: Nominatim (geocoding), OSRM (distance matrix + route geometry), VRPSolverEasy (solver).

**Tech Stack:** Python 3.14, Streamlit 1.57+, streamlit-folium, Folium, geopy (Nominatim), requests (OSRM), VRPSolverEasy, pandas, openpyxl, pytest.

---

## Parallelization Notes

Tasks 2, 3, 4 are INDEPENDENT of each other and can run as parallel subagents after Task 1 is done.

```
Task 0 → Task 1 → [Task 2 ‖ Task 3 ‖ Task 4] → Task 5 → Task 6 → Task 7 → Task 8
```

## File Map

| File | Responsibility |
|---|---|
| `requirements.txt` | All dependencies pinned by minimum version |
| `core/__init__.py` | Empty package marker |
| `core/models.py` | Dataclasses: Ponto, TipoVeiculo, Cenario, Rota, Solucao |
| `core/geocoding.py` | Nominatim geocoding: endereço → (lat, lon) |
| `core/distance.py` | OSRM /table: coords → NxN km matrix |
| `core/routing_geometry.py` | OSRM /route: ordered coords → lat/lon polyline |
| `core/solver.py` | VRPSolverEasy: Cenario + matrix → Solucao |
| `core/mapa.py` | Folium: Solucao + pontos + geometrias → folium.Map |
| `tests/__init__.py` | Empty |
| `tests/test_models.py` | Smoke test for dataclass construction |
| `tests/test_geocoding.py` | Nominatim round-trip and None-on-failure |
| `tests/test_distance.py` | OSRM matrix shape, diagonal, positive values |
| `tests/test_routing_geometry.py` | OSRM polyline format and edge cases |
| `tests/test_solver.py` | Regression (cost=123.198) + multi-depot correctness |
| `tests/test_mapa.py` | Folium map creation without crash |
| `app.py` | Streamlit 3-step wizard UI |

## Key VRPSolverEasy API Facts (verified Python 3.14 / current VRPSolverEasy)

- `model.status == 0` → solução ótima ("The solution found is optimal.")
- `model.status != 0` → inviável/erro — **do NOT use `sol.is_defined`** (it is a method, not a bool)
- `route.cap_consumption` is `list[float]` of cumulative loads; `route.cap_consumption[-1]` = total carga
- `route.point_ids` is `list[int]`; includes depot at start AND end for closed routes
- `route.vehicle_type_id` → which vehicle type served this route
- **Regression baseline** (capacity=500, max=10, cost_per_km=1.0, closed route, dist_matrix_km.xlsx): **cost = 123.198**

---

## Task 0: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `core/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p core tests
touch core/__init__.py tests/__init__.py
```

- [ ] **Step 2: Create requirements.txt**

```
streamlit>=1.57
streamlit-folium>=0.22
folium>=0.17
geopy>=2.4
requests>=2.32
pandas>=2.2
openpyxl>=3.1
VRPSolverEasy
pytest>=8.0
```

- [ ] **Step 3: Install**

```bash
pip install -r requirements.txt
```

Expected: No errors. `streamlit-folium` was previously missing and should now install.

- [ ] **Step 4: Verify all imports**

```bash
python3 -c "
import VRPSolverEasy as vre
import streamlit_folium
import folium
import geopy
import requests
import pandas
print('All imports OK')
"
```

Expected: `All imports OK`

- [ ] **Step 5: Commit**

```bash
git add requirements.txt core/__init__.py tests/__init__.py
git commit -m "feat: project scaffold and requirements"
```

---

## Task 1: Core Models

**Files:**
- Create: `core/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'core.models'`

- [ ] **Step 3: Implement core/models.py**

Create `core/models.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_models.py -v
```

Expected: both tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add core/models.py tests/test_models.py
git commit -m "feat: core data models (Ponto, TipoVeiculo, Cenario, Rota, Solucao)"
```

---

## Task 2: Geocoding Module [PARALLELIZABLE after Task 1]

**Files:**
- Create: `core/geocoding.py`
- Create: `tests/test_geocoding.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_geocoding.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_geocoding.py -v
```

Expected: `ModuleNotFoundError: No module named 'core.geocoding'`

- [ ] **Step 3: Implement core/geocoding.py**

Create `core/geocoding.py`:

```python
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

_geolocator = Nominatim(user_agent="roteirizador-academico-uff")
_geocode = RateLimiter(_geolocator.geocode, min_delay_seconds=1.0)


def geocodificar(endereco: str) -> tuple[float, float] | None:
    try:
        loc = _geocode(endereco)
        if loc is None:
            return None
        return (loc.latitude, loc.longitude)
    except Exception:
        return None


def geocodificar_lote(enderecos: list[str]) -> list[tuple[float, float] | None]:
    return [geocodificar(e) for e in enderecos]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_geocoding.py -v
```

Expected: all 3 tests `PASSED`. (~3s due to rate limiter hitting real Nominatim.)

- [ ] **Step 5: Commit**

```bash
git add core/geocoding.py tests/test_geocoding.py
git commit -m "feat: Nominatim geocoding module with rate limiter"
```

---

## Task 3: Distance Matrix Module [PARALLELIZABLE after Task 1]

**Files:**
- Create: `core/distance.py`
- Create: `tests/test_distance.py`

Note: OSRM expects coordinates as `lon,lat` (longitude first). This module handles the inversion internally so callers always pass `(lat, lon)`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_distance.py`:

```python
import pytest
from core.distance import matriz_distancias

COORDS_NITEROI = [
    (-22.908, -43.131),   # Rua Dr Paulo César (depot ref)
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_distance.py -v
```

Expected: `ModuleNotFoundError: No module named 'core.distance'`

- [ ] **Step 3: Implement core/distance.py**

Create `core/distance.py`:

```python
import requests

OSRM_BASE = "https://router.project-osrm.org"


def matriz_distancias(coords: list[tuple[float, float]]) -> list[list[float]]:
    """
    Retorna matriz NxN de distâncias reais em km via OSRM /table.
    coords: lista de (lat, lon). OSRM espera lon,lat — inversão feita aqui.
    Lança RuntimeError se o serviço estiver indisponível.
    """
    if not coords:
        return []

    coords_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url = f"{OSRM_BASE}/table/v1/driving/{coords_str}?annotations=distance"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"OSRM indisponivel: {exc}") from exc

    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM retornou erro: {data.get('message', data.get('code'))}")

    # 'distances' vem em metros → converter para km
    metros = data["distances"]
    return [[m / 1000.0 for m in linha] for linha in metros]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_distance.py -v
```

Expected: all 4 tests `PASSED`. (~1-2s hitting real OSRM.)

- [ ] **Step 5: Commit**

```bash
git add core/distance.py tests/test_distance.py
git commit -m "feat: OSRM distance matrix module (lon,lat order, meters to km)"
```

---

## Task 4: Solver Module [PARALLELIZABLE after Task 1]

**Files:**
- Create: `core/solver.py`
- Create: `tests/test_solver.py`

Critical reminder: use `model.status == 0` to test for optimality; `sol.is_defined` is a method object (always truthy), NOT a boolean property.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_solver.py`:

```python
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

# Estabelecido em 2026-06-07 rodando VRPSolverEasy direto:
# config: 1 depot (id=0), 1 tipo (cap=500, qty=10, cost=1.0, closed route)
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
    Com a matriz de referência de Niterói e config idêntica ao baseline,
    core/solver.resolver() deve produzir custo 123.198 km (±0.01).
    Garante que a camada core não distorce a matemática do VRPSolverEasy.
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
    Cenário com 2 depósitos (ids 0, 1) e 2 tipos de veículo deve resolver com
    todos os 3 clientes atendidos e sem violar capacidade.
    Usa matriz fixada (não depende do OSRM).
    """
    dist = [
        [0.0, 2.0, 5.0,  8.0, 10.0],  # 0 (dep1)
        [2.0, 0.0, 3.0,  6.0,  8.0],  # 1 (dep2)
        [5.0, 3.0, 0.0,  4.0,  6.0],  # 2 (c1)
        [8.0, 6.0, 4.0,  0.0,  3.0],  # 3 (c2)
        [10.0, 8.0, 6.0, 3.0,  0.0],  # 4 (c3)
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_solver.py -v 2>&1 | tail -5
```

Expected: `ModuleNotFoundError: No module named 'core.solver'`

- [ ] **Step 3: Implement core/solver.py**

Create `core/solver.py`:

```python
import time
import VRPSolverEasy as vre
from core.models import Cenario, Rota, Solucao


def resolver(cenario: Cenario, matriz_dist: list[list[float]]) -> Solucao:
    """
    Constrói e resolve o modelo VRPSolverEasy.
    Retorna Solucao com status "otimo", "inviavel" ou "erro".
    matriz_dist: NxN em km, indexado pela posição em cenario.pontos.
    """
    try:
        return _resolver_interno(cenario, matriz_dist)
    except Exception as exc:
        return Solucao(
            rotas=[], custo_total=0.0, tempo_solucao=0.0,
            status="erro", mensagem=str(exc),
        )


def _resolver_interno(cenario: Cenario, matriz_dist: list[list[float]]) -> Solucao:
    model = vre.Model()

    tipo_por_id = {v.id: v for v in cenario.veiculos}

    # Tipos de veículo
    for v in cenario.veiculos:
        end_pt = v.deposito_id if cenario.retornar_ao_deposito else -1
        model.add_vehicle_type(
            id=v.id,
            start_point_id=v.deposito_id,
            end_point_id=end_pt,
            capacity=v.capacidade,
            max_number=v.quantidade,
            var_cost_dist=v.custo_por_km,
        )

    # Depósitos
    for p in cenario.pontos:
        if p.is_deposito:
            model.add_depot(id=p.id)

    # Clientes
    for p in cenario.pontos:
        if not p.is_deposito:
            model.add_customer(id=p.id, demand=p.demanda)

    # Arcos (dígrafo — matriz pode ser assimétrica)
    for i, pi in enumerate(cenario.pontos):
        for j, pj in enumerate(cenario.pontos):
            if i != j:
                model.add_link(
                    start_point_id=pi.id,
                    end_point_id=pj.id,
                    distance=round(float(matriz_dist[i][j]), 3),
                    is_directed=True,
                )

    t0 = time.time()
    model.set_parameters(solver_name="CLP")
    model.solve()
    tempo = round(time.time() - t0, 3)

    # Usar model.status (não sol.is_defined, que é um método — sempre truthy)
    if model.status != 0:
        return Solucao(
            rotas=[], custo_total=0.0, tempo_solucao=tempo,
            status="inviavel", mensagem=model.message,
        )

    sol = model.solution
    id_to_idx = {p.id: idx for idx, p in enumerate(cenario.pontos)}
    rotas: list[Rota] = []

    for route in sol.routes:
        tipo_id = route.vehicle_type_id
        tipo = tipo_por_id.get(tipo_id)
        nome_tipo = tipo.nome if tipo else f"tipo_{tipo_id}"
        dep_id = tipo.deposito_id if tipo else route.point_ids[0]
        carga = route.cap_consumption[-1] if route.cap_consumption else 0.0
        cap = tipo.capacidade if tipo else 0.0

        seq = list(route.point_ids)
        dist_rota = sum(
            matriz_dist[id_to_idx[seq[k]]][id_to_idx[seq[k + 1]]]
            for k in range(len(seq) - 1)
        )

        rotas.append(Rota(
            veiculo_tipo=nome_tipo,
            deposito_id=dep_id,
            sequencia_ids=seq,
            carga_usada=carga,
            capacidade=cap,
            distancia=round(dist_rota, 3),
        ))

    return Solucao(
        rotas=rotas,
        custo_total=sol.value,
        tempo_solucao=tempo,
        status="otimo",
        mensagem=model.message,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_solver.py -v 2>&1 | grep -E "PASSED|FAILED|ERROR|test_"
```

Expected: both tests `PASSED`. (Solver banner lines will print before the output — that's normal.)

- [ ] **Step 5: Commit**

```bash
git add core/solver.py tests/test_solver.py
git commit -m "feat: VRPSolverEasy solver (multi-depot, heterogeneous fleet, regression=123.198)"
```

---

## Task 5: Routing Geometry Module

**Files:**
- Create: `core/routing_geometry.py`
- Create: `tests/test_routing_geometry.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_routing_geometry.py`:

```python
from core.routing_geometry import geometria_rota

COORDS_SEQUENCIA = [
    (-22.908, -43.131),  # ponto 0
    (-22.892, -43.108),  # ponto 1
    (-22.897, -43.114),  # ponto 2
    (-22.908, -43.131),  # ponto 0 (retorno ao depósito)
]


def test_geometria_rota_retorna_lista_coords():
    poly = geometria_rota(COORDS_SEQUENCIA)
    assert isinstance(poly, list)
    assert len(poly) >= 2
    for pt in poly:
        assert isinstance(pt, tuple)
        assert len(pt) == 2
        lat, lon = pt
        # Bounding box Sul do Brasil (inclui RJ)
        assert -35.0 < lat < -5.0
        assert -55.0 < lon < -30.0


def test_geometria_rota_unico_ponto_retorna_vazio():
    poly = geometria_rota([(-22.908, -43.131)])
    assert poly == []


def test_geometria_rota_lista_vazia_retorna_vazio():
    poly = geometria_rota([])
    assert poly == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_routing_geometry.py -v
```

Expected: `ModuleNotFoundError: No module named 'core.routing_geometry'`

- [ ] **Step 3: Implement core/routing_geometry.py**

Create `core/routing_geometry.py`:

```python
import requests

OSRM_BASE = "https://router.project-osrm.org"


def geometria_rota(coords_ordenadas: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """
    Dado a sequência ordenada de (lat, lon) de uma rota, retorna a polilinha
    real das ruas via OSRM /route?overview=full&geometries=geojson.
    Retorna lista de (lat, lon). Em caso de erro ou entrada insuficiente,
    retorna lista vazia (nunca lança exceção).
    """
    if len(coords_ordenadas) < 2:
        return []

    # OSRM espera lon,lat
    coords_str = ";".join(f"{lon},{lat}" for lat, lon in coords_ordenadas)
    url = (
        f"{OSRM_BASE}/route/v1/driving/{coords_str}"
        "?overview=full&geometries=geojson"
    )

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return []

    if data.get("code") != "Ok" or not data.get("routes"):
        return []

    # GeoJSON coordinates são [lon, lat] → inverter para (lat, lon)
    geojson_coords = data["routes"][0]["geometry"]["coordinates"]
    return [(lat, lon) for lon, lat in geojson_coords]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_routing_geometry.py -v
```

Expected: all 3 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add core/routing_geometry.py tests/test_routing_geometry.py
git commit -m "feat: OSRM route geometry module (geojson polyline, lat/lon inversion)"
```

---

## Task 6: Map Module

**Files:**
- Create: `core/mapa.py`
- Create: `tests/test_mapa.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_mapa.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_mapa.py -v
```

Expected: `ModuleNotFoundError: No module named 'core.mapa'`

- [ ] **Step 3: Implement core/mapa.py**

Create `core/mapa.py`:

```python
import folium
from core.models import Ponto, Solucao

_PALETA = [
    "#c0392b", "#2980b9", "#27ae60", "#8e44ad", "#e67e22",
    "#16a085", "#d35400", "#2c3e50", "#f39c12", "#1abc9c",
]


def desenhar(
    solucao: Solucao,
    pontos: list[Ponto],
    geometrias: dict[int, list[tuple[float, float]]],
) -> folium.Map:
    """
    geometrias: índice da rota (0-based) → lista de (lat, lon) seguindo as ruas.
    """
    lats = [p.lat for p in pontos if p.lat is not None]
    lons = [p.lon for p in pontos if p.lon is not None]
    centro = (
        (sum(lats) / len(lats), sum(lons) / len(lons))
        if lats else (-22.9, -43.1)
    )

    m = folium.Map(location=centro, zoom_start=13)

    for p in pontos:
        if p.lat is None or p.lon is None:
            continue
        if p.is_deposito:
            folium.Marker(
                location=[p.lat, p.lon],
                tooltip=f"Deposito: {p.endereco}",
                icon=folium.Icon(color="black", icon="home"),
            ).add_to(m)
        else:
            folium.Marker(
                location=[p.lat, p.lon],
                tooltip=f"Cliente {p.id}: {p.endereco} (demanda={p.demanda:.0f})",
                icon=folium.Icon(color="blue", icon="info-sign"),
            ).add_to(m)

    for k, rota in enumerate(solucao.rotas):
        cor = _PALETA[k % len(_PALETA)]
        poly = geometrias.get(k)
        if poly:
            folium.PolyLine(
                locations=poly,
                color=cor,
                weight=4,
                tooltip=(
                    f"Rota {k + 1} | {rota.veiculo_tipo} | "
                    f"Carga: {rota.carga_usada:.0f}/{rota.capacidade:.0f} | "
                    f"Dist: {rota.distancia:.1f} km"
                ),
            ).add_to(m)

    return m
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_mapa.py -v
```

Expected: both tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add core/mapa.py tests/test_mapa.py
git commit -m "feat: Folium map with route polylines, depot/client markers, color palette"
```

---

## Task 7: Streamlit UI

**Files:**
- Create: `app.py`

This task cannot be unit-tested with pytest. Verification is manual in Task 8.

- [ ] **Step 1: Create app.py**

Create `app.py`:

```python
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from core.distance import matriz_distancias
from core.geocoding import geocodificar_lote
from core.mapa import desenhar
from core.models import Cenario, Ponto, TipoVeiculo
from core.routing_geometry import geometria_rota
from core.solver import resolver

st.set_page_config(page_title="Roteirizador CVRP", layout="wide")


def _init_state():
    defaults = {
        "etapa": 1,
        "pontos": [],
        "veiculos": [],
        "retornar_ao_deposito": True,
        "solucao": None,
        "geometrias": {},
        "df_enderecos": pd.DataFrame({
            "endereco": ["", "", ""],
            "demanda": [0.0, 100.0, 80.0],
            "deposito": [True, False, False],
        }),
        "df_frota": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


def _barra_progresso():
    etapa = st.session_state.etapa
    cols = st.columns(3)
    rotulos = ["1. Enderecos", "2. Frota", "3. Resultado"]
    for i, (col, rotulo) in enumerate(zip(cols, rotulos)):
        if i + 1 == etapa:
            col.markdown(f"**{rotulo}**")
        else:
            col.markdown(rotulo)


_barra_progresso()
st.divider()


# ── Etapa 1 ──────────────────────────────────────────────────────────────────

def _etapa_1():
    st.header("Etapa 1: Enderecos")
    st.caption(
        "Informe os pontos de entrega. "
        "Marque 'Deposito' em ao menos um ponto. "
        "Clientes devem ter demanda > 0."
    )

    df_editado = st.data_editor(
        st.session_state.df_enderecos,
        num_rows="dynamic",
        column_config={
            "endereco": st.column_config.TextColumn("Endereco", width="large"),
            "demanda": st.column_config.NumberColumn("Demanda", min_value=0, step=1.0),
            "deposito": st.column_config.CheckboxColumn("Deposito"),
        },
        use_container_width=True,
        key="editor_enderecos",
    )
    st.session_state.df_enderecos = df_editado

    validos = df_editado[df_editado["endereco"].str.strip() != ""]
    tem_deposito = bool(validos["deposito"].any())
    tem_cliente = bool((~validos["deposito"] & (validos["demanda"] > 0)).any())

    if not tem_deposito:
        st.warning("Marque ao menos um ponto como deposito.")
    if not tem_cliente:
        st.warning("Adicione ao menos um cliente com demanda > 0.")

    pode_avancar = tem_deposito and tem_cliente and len(validos) >= 2

    if st.button("Geocodificar e Avancar", disabled=not pode_avancar, type="primary"):
        enderecos = validos["endereco"].tolist()
        with st.spinner("Geocodificando enderecos (1 s por endereco)..."):
            coords = geocodificar_lote(enderecos)

        falhas = [e for e, c in zip(enderecos, coords) if c is None]
        if falhas:
            for f in falhas:
                st.error(f"Endereco nao encontrado: {f}")
            return

        pontos = []
        for idx, (_, row) in enumerate(validos.iterrows()):
            lat, lon = coords[idx]
            pontos.append(Ponto(
                id=idx,
                endereco=str(row["endereco"]),
                lat=lat,
                lon=lon,
                is_deposito=bool(row["deposito"]),
                demanda=0.0 if bool(row["deposito"]) else float(row["demanda"]),
            ))

        st.session_state.pontos = pontos
        st.session_state.df_frota = None   # reset frota ao mudar pontos
        st.session_state.etapa = 2
        st.rerun()


# ── Etapa 2 ──────────────────────────────────────────────────────────────────

def _etapa_2():
    st.header("Etapa 2: Frota")
    pontos = st.session_state.pontos
    depositos = [p for p in pontos if p.is_deposito]
    opcoes_deposito = [p.endereco for p in depositos]
    demanda_total = sum(p.demanda for p in pontos if not p.is_deposito)

    st.caption(f"Demanda total dos clientes: {demanda_total:.0f} unidades")

    if st.session_state.df_frota is None:
        st.session_state.df_frota = pd.DataFrame({
            "tipo": ["Van"],
            "capacidade": [500.0],
            "quantidade": [2],
            "custo_por_km": [1.0],
            "deposito": [opcoes_deposito[0] if opcoes_deposito else ""],
        })

    df_frota = st.data_editor(
        st.session_state.df_frota,
        num_rows="dynamic",
        column_config={
            "tipo": st.column_config.TextColumn("Tipo", width="small"),
            "capacidade": st.column_config.NumberColumn("Capacidade", min_value=1, step=50.0),
            "quantidade": st.column_config.NumberColumn("Qtd", min_value=1, step=1),
            "custo_por_km": st.column_config.NumberColumn("Custo/km", min_value=0.0, step=0.1),
            "deposito": st.column_config.SelectboxColumn(
                "Deposito de origem", options=opcoes_deposito
            ),
        },
        use_container_width=True,
        key="editor_frota",
    )
    st.session_state.df_frota = df_frota

    retornar = st.toggle(
        "Veiculos retornam ao deposito de origem",
        value=st.session_state.retornar_ao_deposito,
    )
    st.session_state.retornar_ao_deposito = retornar

    cap_total = float((df_frota["capacidade"] * df_frota["quantidade"]).sum())
    frota_ok = cap_total >= demanda_total

    if not frota_ok:
        st.error(
            f"Frota insuficiente: demanda {demanda_total:.0f} > capacidade total {cap_total:.0f}"
        )
    else:
        st.success(f"Capacidade total: {cap_total:.0f}  |  Demanda: {demanda_total:.0f}")

    col_v, col_c = st.columns([1, 5])
    with col_v:
        if st.button("Voltar"):
            st.session_state.etapa = 1
            st.rerun()
    with col_c:
        if st.button("Calcular Rota", disabled=not frota_ok, type="primary"):
            dep_por_endereco = {p.endereco: p.id for p in depositos}
            veiculos = []
            for idx, (_, row) in enumerate(df_frota.iterrows()):
                dep_id = dep_por_endereco.get(str(row["deposito"]), depositos[0].id)
                veiculos.append(TipoVeiculo(
                    id=idx + 1,
                    nome=str(row["tipo"]),
                    capacidade=float(row["capacidade"]),
                    quantidade=int(row["quantidade"]),
                    custo_por_km=float(row["custo_por_km"]),
                    deposito_id=dep_id,
                ))
            st.session_state.veiculos = veiculos
            st.session_state.solucao = None
            st.session_state.etapa = 3
            st.rerun()


# ── Etapa 3 ──────────────────────────────────────────────────────────────────

def _etapa_3():
    st.header("Etapa 3: Resultado")
    pontos = st.session_state.pontos
    veiculos = st.session_state.veiculos

    if st.session_state.solucao is None:
        cenario = Cenario(
            pontos=pontos,
            veiculos=veiculos,
            retornar_ao_deposito=st.session_state.retornar_ao_deposito,
        )
        with st.spinner("Calculando matriz de distancias (OSRM)..."):
            try:
                coords = [(p.lat, p.lon) for p in pontos]
                matriz = matriz_distancias(coords)
            except RuntimeError as exc:
                st.error(f"Servico de rotas indisponivel: {exc}")
                return

        with st.spinner("Resolvendo CVRP (VRPSolverEasy)..."):
            sol = resolver(cenario, matriz)
        st.session_state.solucao = sol

        if sol.status == "otimo":
            with st.spinner("Obtendo geometria das rotas (OSRM)..."):
                id_to_coord = {p.id: (p.lat, p.lon) for p in pontos}
                geoms: dict[int, list[tuple[float, float]]] = {}
                for k, rota in enumerate(sol.rotas):
                    seq_coords = [
                        id_to_coord[pid]
                        for pid in rota.sequencia_ids
                        if pid in id_to_coord
                    ]
                    geoms[k] = geometria_rota(seq_coords)
            st.session_state.geometrias = geoms

    sol = st.session_state.solucao

    if sol.status != "otimo":
        msg = "Solucao inviavel" if sol.status == "inviavel" else "Erro no solver"
        st.error(f"{msg}: {sol.mensagem}")
        if st.button("Voltar e ajustar"):
            st.session_state.etapa = 2
            st.rerun()
        return

    col_mapa, col_resumo = st.columns([3, 1])

    with col_resumo:
        st.subheader("Resumo")
        st.metric("Custo total", f"{sol.custo_total:.2f} km")
        st.metric("Tempo solver", f"{sol.tempo_solucao:.2f} s")
        st.metric("Rotas geradas", len(sol.rotas))
        st.caption(sol.mensagem)
        st.divider()
        for k, rota in enumerate(sol.rotas):
            st.markdown(
                f"**Rota {k + 1}** — {rota.veiculo_tipo}  \n"
                f"Deposito: {rota.deposito_id}  \n"
                f"Carga: {rota.carga_usada:.0f} / {rota.capacidade:.0f}  \n"
                f"Distancia: {rota.distancia:.1f} km"
            )

    with col_mapa:
        mapa = desenhar(sol, pontos, st.session_state.geometrias)
        st_folium(mapa, width=800, height=550, returned_objects=[])

    if st.button("Voltar e recalcular"):
        st.session_state.solucao = None
        st.session_state.etapa = 2
        st.rerun()


# ── Despacho ─────────────────────────────────────────────────────────────────

if st.session_state.etapa == 1:
    _etapa_1()
elif st.session_state.etapa == 2:
    _etapa_2()
elif st.session_state.etapa == 3:
    _etapa_3()
```

- [ ] **Step 2: Verify syntax**

```bash
python3 -m py_compile app.py && echo "Syntax OK"
```

Expected: `Syntax OK`

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: Streamlit 3-step wizard (geocoding, fleet table, VRP result + Folium map)"
```

---

## Task 8: End-to-End Verification

**Files:** No new files.

- [ ] **Step 1: Run full core test suite**

```bash
pytest tests/test_models.py tests/test_solver.py tests/test_mapa.py -v 2>&1 | grep -E "PASSED|FAILED|ERROR"
```

Expected: all tests `PASSED`.

- [ ] **Step 2: Launch the app**

```bash
streamlit run app.py
```

Expected: Browser opens at http://localhost:8501 showing "Etapa 1: Enderecos".

- [ ] **Step 3: Teste caminho de erro — endereco invalido**

1. Na Etapa 1, deixe a tabela com "Rua XYZ Inexistente 99999" como cliente.
2. Clique "Geocodificar e Avancar".
3. **Esperado:** mensagem vermelha "Endereco nao encontrado: Rua XYZ..."; app não avança.

- [ ] **Step 4: Teste caminho de erro — sem deposito**

1. Preencha 3 enderecos validos mas sem nenhuma caixa "Deposito" marcada.
2. **Esperado:** warning "Marque ao menos um ponto como deposito"; botao desabilitado.

- [ ] **Step 5: Teste caminho de erro — frota insuficiente**

1. Avance para Etapa 2 com demanda total > 0.
2. Defina 1 Van com capacidade=1 e quantidade=1.
3. **Esperado:** mensagem vermelha "Frota insuficiente: demanda X > capacidade Y"; "Calcular Rota" desabilitado.

- [ ] **Step 6: Teste cenário baseline — 1 depot, 1 tipo**

1. Na Etapa 1, insira os 21 pontos da referência (arquivo `../Trabalho_final/criar_enderecos.py`):
   - Ponto 0: "Rua Doutor Paulo César, 235 - Santa Rosa, Niterói - RJ, Brasil" → marcar Deposito, demanda 0
   - Pontos 1-20: enderecos dos arquivos, demandas: 120, 80, 150, 200, 90, 110, 130, 70, 100, 60, 140, 50, 160, 180, 75, 95, 85, 65, 55, 125
2. Na Etapa 2: 1 Van (cap=500, qty=10, cost=1.0, depot=ponto 0), toggle retorno=ON.
3. Calcular.
4. **Esperado:** custo exibido ~123.20 km; 5 rotas no painel; rotas seguem ruas no mapa.

- [ ] **Step 7: Teste cenário multi-depot**

1. Voltar para Etapa 1 e marcar DOIS depósitos:
   - Ponto 0: "Rua Doutor Paulo César, 235 - Santa Rosa, Niterói - RJ, Brasil"
   - Ponto 15: "Avenida Rio Branco, 257 - Centro, Rio de Janeiro - RJ, Brasil"
2. Na Etapa 2: adicionar 2 tipos:
   - "Van Niteroi": cap=500, qty=3, cost=1.0, depot=ponto 0
   - "Van Rio": cap=500, qty=3, cost=1.0, depot=ponto 15
3. Calcular.
4. **Esperado:** rotas saindo de ambos os depósitos; cores distintas; carga ≤ capacidade em todas.

- [ ] **Step 8: Verificar ausência de APIs pagas e emojis**

```bash
grep -rn "google\|openrouteservice\|mapbox\|api_key\|APIKey" app.py core/ && echo "FAIL" || echo "OK: sem API paga"
```

```bash
python3 -c "
import re, sys
text = open('app.py').read() + open('core/solver.py').read() + open('core/mapa.py').read()
found = re.findall(r'[\U00010000-\U0010ffff]|\U0001F[0-9A-F]{3}', text)
print('FAIL emojis:', found) if found else print('OK: sem emojis')
"
```

Expected: both `OK`.

- [ ] **Step 9: Commit final**

```bash
git add -A
git commit -m "feat: MVP completo — roteirizador CVRP multi-deposito, Folium map, VRPSolverEasy"
```

---

## Definition of Done

- [ ] `pytest tests/test_models.py tests/test_solver.py tests/test_mapa.py` — todos PASSED
- [ ] Teste de regressão do solver bate com baseline 123.198 ± 0.01
- [ ] App roda em localhost e percorre as 3 etapas sem crash
- [ ] Cenário multi-depósito + frota heterogênea produz rotas corretas
- [ ] Rotas desenhadas seguindo ruas reais (polilinha OSRM, não linha reta)
- [ ] Todos os caminhos de erro mostram mensagem amigável, sem crash
- [ ] Nenhuma chamada a serviço pago; nenhuma chave de API
- [ ] Sem emojis na interface
