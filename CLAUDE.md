# Orientação para implementação — leia isto primeiro

Você é o Claude que vai **implementar** este projeto numa sessão de contexto limpo. Esta pasta
(`roteirizador/`) contém a especificação completa de um MVP já validada com o usuário num
brainstorming anterior. **Não refaça o brainstorming.** O design está fechado; seu trabalho é
planejar a implementação e executá-la com qualidade.

## Ordem de leitura recomendada

1. `docs/DESIGN.md` — entenda o produto, o escopo e **por que** cada decisão foi tomada.
2. `docs/ARCHITECTURE.md` — entenda a estrutura de módulos e os contratos entre eles.
3. `docs/TECH_STACK.md` — conheça as bibliotecas e os limites dos serviços gratuitos.
4. `docs/REFERENCE.md` — tenha à mão a API real do VRPSolverEasy e os endpoints OSRM/Nominatim.
5. `docs/BUILD_PLAN.md` — siga (ou refine) o plano de fases.

## Processo esperado (superpowers)

O usuário quer que você execute com **subagentes**, usando as skills do superpowers:

1. Invoque **`superpowers:writing-plans`** para transformar `docs/BUILD_PLAN.md` num plano de
   implementação detalhado (tarefas pequenas, verificáveis, com critérios de aceite).
2. Invoque **`superpowers:subagent-driven-development`** (ou `executing-plans`) para executar as
   tarefas independentes em paralelo, mantendo o contexto principal limpo.
3. Use **`superpowers:test-driven-development`** ao implementar cada módulo do `core/`.
4. Use **`superpowers:verification-before-completion`** antes de declarar qualquer coisa pronta —
   evidência antes de afirmação.

## Restrições inegociáveis (decididas com o usuário)

- **100% Python.** Nada de JS/HTML/CSS escritos à mão. O mapa é renderizado por Folium (Python).
- **Custo zero.** Nada de Google Maps API nem qualquer serviço pago. Geocoding = Nominatim;
  distâncias e geometria = OSRM. Sem chaves de API.
- **VRPSolverEasy é o único solver.** É um requisito acadêmico — não troque por OR-Tools ou outro.
- **Multi-depósito + frota heterogênea** são requisitos centrais, não "nice-to-have".
- **Sem emojis** na interface.
- Roda em **localhost** (Streamlit). Deploy em nuvem está fora do escopo do MVP (ver DESIGN.md §Fora de escopo).

## Onde reaproveitar código existente

A pasta irmã `../Trabalho_final/` contém o pipeline original (notebook + scripts). O modelo
VRPSolverEasy já funciona lá. **Leia `docs/REFERENCE.md`** para o mapeamento exato do que copiar
e do que adaptar (especialmente a construção do modelo no `notebook_tf.ipynb`).

## Princípio

Simplicidade primeiro, sem gambiarra, impacto mínimo. Cada módulo do `core/` deve ter uma única
responsabilidade e ser testável isoladamente. Se um arquivo cresce demais, ele está fazendo coisa
demais — divida.
