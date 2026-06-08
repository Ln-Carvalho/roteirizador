# BUILD_PLAN — Roteirizador

> Plano de implementação em fases, pensado para execução com **subagentes** (superpowers).
> Não é o plano final: o próximo Claude deve rodar `superpowers:writing-plans` para transformar
> isto em tarefas detalhadas com critérios de aceite, e então executar. Este documento dá a
> espinha dorsal e a ordem de dependências.

---

## Estratégia geral

- Construa o **`core/` antes da UI**. Cada módulo do core é independente e testável → bom candidato
  a **subagente paralelo** depois que `models.py` existir.
- Aplique **TDD** em cada módulo do core (`superpowers:test-driven-development`).
- A UI (`app.py`) entra por último, apenas orquestrando módulos prontos.
- **Verifique cada fase** com evidência real (`superpowers:verification-before-completion`) antes de
  seguir.

## Grafo de dependências

```
Fase 0 (setup) ──► Fase 1 (models.py) ──┬──► Fase 2a (geocoding)   ┐
                                        ├──► Fase 2b (distance)    ├─► Fase 3 (solver) ──► Fase 4 (mapa) ──► Fase 5 (app.py) ──► Fase 6 (E2E)
                                        └──► (independentes)       ┘
```

Fases 2a e 2b são **independentes entre si** → podem ir para subagentes paralelos.
A Fase 3 (solver) depende de `models.py` (Fase 1) e da matriz (contrato da Fase 2b), mas pode ser
desenvolvida e testada com a **matriz fixa** de `dist_matrix_km.xlsx` sem esperar o módulo de
distância real → também paralelizável com as Fases 2a/2b.

---

## Fase 0 — Setup do projeto
- Criar `requirements.txt`, `core/__init__.py`, esqueleto de pastas, `tests/`.
- Confirmar que `import VRPSolverEasy` funciona no ambiente (o notebook já roda → deve funcionar).
- **Aceite:** `pip install -r requirements.txt` instala tudo; `python -c "import VRPSolverEasy"` ok.

## Fase 1 — Modelo de dados (`core/models.py`)
- Implementar as dataclasses de `ARCHITECTURE.md §2` (`Ponto`, `TipoVeiculo`, `Cenario`, `Rota`,
  `Solucao`).
- **Aceite:** dataclasses importáveis; um `Cenario` de exemplo é construível em um teste.
- *Bloqueia todas as fases seguintes — faça primeiro, sozinho.*

## Fase 2a — Geocoding (`core/geocoding.py`)  ⟂ paralelo
- `geocodificar` / `geocodificar_lote` via Nominatim + `RateLimiter` (TECH_STACK §2).
- Tratar retorno vazio como `None` (endereço não encontrado).
- **Aceite:** `tests/test_geocoding.py` geocodifica um endereço conhecido de Niterói e confere que
  lat/lon caem numa caixa geográfica plausível; endereço falso retorna `None`.

## Fase 2b — Matriz de distância (`core/distance.py`)  ⟂ paralelo
- `matriz_distancias(coords)` via OSRM `/table?annotations=distance` (TECH_STACK §3).
- Atenção à ordem `lon,lat`; converter metros → km.
- Tratar indisponibilidade do OSRM com exceção clara.
- **Aceite:** `tests/test_distance.py` — para um punhado de coordenadas reais, retorna matriz NxN
  com diagonal ~0 e valores positivos coerentes (compare a ordem de grandeza com `dist_matrix_km.xlsx`).

## Fase 3 — Solver (`core/solver.py`)  ⟂ paralelo (usa matriz fixa nos testes)
- `resolver(cenario, matriz_dist) -> Solucao` construindo o modelo VRPSolverEasy conforme
  `REFERENCE.md §1` (multi-depósito + frota heterogênea + toggle de retorno).
- Mapear `model.solution.routes` → `list[Rota]`; preencher status/mensagem/tempo.
- **Aceite (regressão):** `tests/test_solver.py` reproduz o custo do notebook para a config
  1-depósito/1-veículo sobre `dist_matrix_km.xlsx` (REFERENCE §3). **Este é o teste mais importante.**
- **Aceite (multi-depósito):** um cenário com 2 depósitos + 2 tipos de veículo resolve e devolve
  rotas saindo de ambos os depósitos, com `carga_usada ≤ capacidade` em toda rota.

## Fase 4 — Geometria + Mapa (`core/routing_geometry.py` + `core/mapa.py`)
- `geometria_rota` via OSRM `/route?overview=full&geometries=geojson`; inverter para `(lat,lon)`.
- `desenhar(solucao, pontos, geometrias) -> folium.Map`: marcadores (depósito vs cliente), uma cor
  por rota, polilinhas com a geometria real.
- **Aceite:** dado uma `Solucao` de exemplo, gera um `folium.Map` sem erro; salvar em HTML mostra as
  rotas seguindo ruas (inspeção visual).

## Fase 5 — Interface (`app.py`)
- Wizard de 3 etapas (DESIGN §5) com `st.session_state` (ARCHITECTURE §6).
- Etapa 1: tabela editável de endereços (`st.data_editor`) com coluna de depósito; geocoding ao
  avançar; destaque de falhas; validações.
- Etapa 2: tabela editável de tipos de veículo + toggle global; validação de capacidade vs demanda.
- Etapa 3: botão "Calcular" → fluxo completo (ARCHITECTURE §3) → `st_folium` + painel de resumo;
  botão "Voltar" para recalcular.
- Tratamento de erros sempre como mensagem amigável (nunca crash).
- **Aceite:** percorrer as 3 etapas em localhost produz mapa + resumo.

## Fase 6 — Verificação ponta a ponta (E2E)
- Rodar `streamlit run app.py` e executar o **cenário multi-depósito de demonstração**
  (REFERENCE §4) do início ao fim.
- Conferir os **critérios de aceite do MVP** (DESIGN §6), um a um, com evidência.
- Conferir os caminhos de erro: endereço inválido, frota insuficiente, sem depósito.

---

## Checklist final (Definition of Done do MVP)

- [ ] `core/` completo, cada módulo com teste passando.
- [ ] Teste de regressão do solver bate com o baseline do notebook.
- [ ] App roda em localhost e percorre as 3 etapas.
- [ ] Cenário multi-depósito + frota heterogênea produz rotas corretas no mapa.
- [ ] Rotas desenhadas seguindo as ruas (não linha reta).
- [ ] Todos os caminhos de erro mostram mensagem amigável, sem crash.
- [ ] Nenhuma chave de API; nenhuma chamada a serviço pago.
- [ ] Sem emojis na interface.
- [ ] `README.md` atualizado com instruções reais de execução.
