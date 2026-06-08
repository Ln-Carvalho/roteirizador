# Roteirizador — Otimizador de Rotas (CVRP) com interface web

Aplicação web **100% Python** que resolve o **Problema de Roteamento de Veículos com Capacidade (CVRP)**
com **múltiplos depósitos** e **frota heterogênea**, usando o solver acadêmico **VRPSolverEasy**,
e desenha as rotas otimizadas num mapa interativo para o usuário auditar a solução.

Projeto acadêmico (Tópico I — Roteamento de Veículos). Roda em **localhost** via Streamlit.
Não depende de nenhuma API paga: geocoding e distâncias vêm de serviços gratuitos baseados em OpenStreetMap.

---

## O que o usuário faz (fluxo em 3 etapas)

1. **Endereços** — informa os pontos de entrega (texto), a demanda de cada um, e marca quais pontos
   são depósitos (pode marcar mais de um). Depósitos não têm demanda.
2. **Frota** — cadastra os tipos de veículo (capacidade, quantidade, custo por km) e associa cada
   tipo a um depósito de origem. Define se os veículos voltam ao depósito ao final da rota.
3. **Resultado** — vê as rotas ótimas coloridas no mapa (seguindo as ruas reais) e um resumo com
   custo total, carga usada por rota e tempo de solução.

---

## Stack (toda em Python)

| Camada | Biblioteca / Serviço | Custo |
|---|---|---|
| Interface (wizard) | Streamlit | grátis |
| Geocoding (endereço → lat/lon) | Nominatim via `geopy` | grátis, sem chave |
| Matriz de distância + geometria das rotas | OSRM (servidor público OpenStreetMap) | grátis, sem chave |
| Solver CVRP | VRPSolverEasy (Branch-Cut-and-Price, solver CLP) | grátis (licença acadêmica) |
| Mapa interativo | Folium + streamlit-folium | grátis |

---

## Como rodar (quando estiver implementado)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abra `http://localhost:8501`.

---

## Status

🟡 **Especificação concluída — implementação não iniciada.**

Esta pasta contém **apenas a documentação de design** do MVP. A implementação será feita numa
sessão dedicada. Comece lendo **[`CLAUDE.md`](./CLAUDE.md)**, que orienta a ordem de leitura e o
processo de execução.

---

## Mapa da documentação

| Documento | Para quê |
|---|---|
| [`CLAUDE.md`](./CLAUDE.md) | Orientação para quem vai implementar — leia primeiro |
| [`docs/DESIGN.md`](./docs/DESIGN.md) | O quê e por quê: visão, escopo, UX do wizard, decisões |
| [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) | Como: módulos, fluxo de dados, contratos, erros, estado |
| [`docs/TECH_STACK.md`](./docs/TECH_STACK.md) | Bibliotecas, stack OSM gratuito e seus limites |
| [`docs/REFERENCE.md`](./docs/REFERENCE.md) | Referência concreta: API do solver, endpoints, código a reaproveitar |
| [`docs/BUILD_PLAN.md`](./docs/BUILD_PLAN.md) | Plano de implementação em fases + estratégia de verificação |
