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

🟢 **Implementacao concluida e validada.**

O MVP foi implementado com sucesso incluindo as logicas adicionais de Multiplas Viagens por Veiculo (MTVRP) e trava de seguranca de demandas.

---

## Creditos e Agradecimentos

Este projeto foi desenvolvido por **Luan Carvalho** para a disciplina de **Topicos em Engenharia de Producao da UFF - TEP00132**, ministrada pelo **Professor Eduardo Uchoa**.

Um agradecimento especial a excelente biblioteca **VRPSolverEasy** por fornecer uma interface acessivel e robusta para modelagem matematica de problemas de roteamento. Seu uso foi fundamental para viabilizar as solucoes exatas deste trabalho.

---

## Mapa da documentacao

| Documento | Para que |
|---|---|
| [`CLAUDE.md`](./CLAUDE.md) | Orientacao para quem vai implementar — leia primeiro |
| [`docs/DESIGN.md`](./docs/DESIGN.md) | O que e por que: visao, escopo, UX do wizard, decisoes |
| [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) | Como: modulos, fluxo de dados, contratos, erros, estado |
| [`docs/TECH_STACK.md`](./docs/TECH_STACK.md) | Bibliotecas, stack OSM gratuito e seus limites |
| [`docs/REFERENCE.md`](./docs/REFERENCE.md) | Referencia concreta: API do solver, endpoints, codigo a reaproveitar |
| [`docs/BUILD_PLAN.md`](./docs/BUILD_PLAN.md) | Plano de implementacao em fases + estrategia de verificacao |
| [`docs/FEEDBACK.md`](./docs/FEEDBACK.md) | Registros de melhorias pos-MVP |
