# DESIGN — Roteirizador (CVRP multi-depósito, frota heterogênea)

> Documento de design do MVP. Resultado de um brainstorming validado com o usuário em 2026-06-07.
> Status: **aprovado**. Este é o contrato do produto — implemente conforme aqui descrito.

---

## 1. Visão

Uma aplicação web local que permite a um usuário não-programador montar um problema de roteamento
de veículos (endereços, demandas, depósitos, frota), resolvê-lo com um solver exato de qualidade
acadêmica (VRPSolverEasy) e **auditar visualmente** a solução ótima num mapa antes de confiar nela.

O diferencial sobre o pipeline original (notebook Jupyter) é tornar tudo **interativo, visual e
acessível** — sem editar código, sem chaves de API pagas, rodando em localhost.

## 2. Objetivos do MVP

- O usuário informa **endereços em texto**, e o sistema os converte em coordenadas automaticamente.
- O usuário marca **um ou mais depósitos** entre os endereços.
- O usuário define uma **frota heterogênea** (vários tipos de veículo com capacidade, quantidade e
  custo/km distintos), cada tipo associado a um depósito de origem.
- O usuário escolhe se os **veículos voltam ao depósito** ao final.
- O sistema calcula a **rota de custo mínimo** com o VRPSolverEasy.
- O sistema **desenha as rotas no mapa** seguindo as ruas reais, com um resumo numérico, para
  auditoria.
- **Custo zero** de operação (sem APIs pagas) e **100% Python**.

## 3. Fora de escopo (MVP) — YAGNI

Estas ideias são boas, mas **não** entram no MVP. Não as implemente sem pedido explícito:

- Deploy em nuvem (Streamlit Cloud) e a questão da licença do VRPSolverEasy na nuvem.
- Janelas de tempo (time windows) — apesar de o VRPSolverEasy suportar.
- Entrada de endereços por clique no mapa ou upload de planilha (decidiu-se por **texto**).
- Frota com restrições de compatibilidade veículo↔cliente.
- Persistência de cenários / contas de usuário / histórico.
- Otimização multiobjetivo, métricas de CO₂, etc.
- "Voltar ao depósito" configurável por tipo de veículo (decidiu-se por **toggle global**).

## 4. Decisões de design e seus porquês

Cada decisão abaixo foi tomada com o usuário. O **porquê** existe para que a implementação não as
reverta por engano.

| # | Decisão | Por quê |
|---|---|---|
| D1 | **Entrada por texto** (digitar endereços) | Mais próximo do pipeline atual; geocoding automático resolve o resto. |
| D2 | **Stack OpenStreetMap gratuito** (Nominatim + OSRM) em vez de Google | Evita custo de API; o usuário não quer pagar nem exigir que o usuário final pague. OSRM ainda entrega a geometria real das ruas de graça. |
| D3 | **Frota heterogênea** (vários tipos de veículo) | É um trabalho acadêmico — quer demonstrar o modelo mais geral, não o caso simplificado. |
| D4 | **Multi-depósito** | O VRPSolverEasy suporta nativamente; aumenta o realismo e o valor acadêmico. |
| D5 | **Wizard de 3 etapas** (Endereços → Frota → Resultado) | Mais didático para apresentação acadêmica do que um painel denso. |
| D6 | **Depósito é uma coluna na etapa de Endereços**, não uma etapa própria | Marcar o depósito é parte de informar os pontos; uma etapa só para isso não se justifica. |
| D7 | **Cada tipo de veículo é associado a um depósito** | É como o VRPSolverEasy amarra frota a depósito (`start_point_id`/`end_point_id`). |
| D8 | **Toggle "voltar ao depósito" global** | Caso clássico do CVRP; configurar por veículo seria complexidade desnecessária no MVP. |
| D9 | **Sem emojis** na interface | Preferência do usuário. |
| D10 | **Mapa renderizado com Folium** | Mantém 100% Python; Folium gera o mapa Leaflet/OSM sem tocar em JS. |

## 5. UX — especificação do wizard

Wizard de **3 etapas** em Streamlit, com indicador de progresso no topo. Estado mantido em
`st.session_state` para que o usuário navegue entre etapas (avançar/voltar) sem perder dados.

### Etapa 1 — Endereços

Uma tabela editável onde cada linha representa um ponto:

| Coluna | Tipo | Regras |
|---|---|---|
| `endereço` | texto | obrigatório; será geocodificado |
| `demanda` | número ≥ 0 | obrigatório para clientes; ignorado/vazio para depósitos |
| `depósito` | booleano (checkbox) | pode ser marcado em **mais de uma** linha; ao menos um obrigatório |

- O usuário adiciona/remove linhas livremente.
- Depósitos não têm demanda (a UI desabilita ou ignora o campo demanda quando `depósito = true`).
- Ao avançar, o sistema **geocodifica** todos os endereços. Linhas que falharem são destacadas em
  vermelho com a mensagem "endereço não encontrado" e o usuário corrige antes de prosseguir.
- Validações para avançar: ≥ 1 depósito marcado **e** ≥ 1 cliente (não-depósito) com demanda > 0.

### Etapa 2 — Frota

Uma tabela editável de **tipos de veículo**:

| Coluna | Tipo | Regras |
|---|---|---|
| `tipo` (nome) | texto | rótulo livre (ex.: "Moto", "Van") |
| `capacidade` | número > 0 | capacidade de carga do veículo |
| `quantidade` | inteiro > 0 | nº máximo de veículos desse tipo |
| `custo_por_km` | número ≥ 0 | custo variável por km (objetivo a minimizar) |
| `depósito` | seleção | qual depósito (da Etapa 1) é a origem deste tipo |

- Abaixo da tabela, um único toggle global: **"veículos voltam ao seu depósito de origem"**.
- Validação para avançar: a **capacidade total da frota** (Σ capacidade × quantidade) deve ser ≥
  **demanda total** dos clientes. Caso contrário, mensagem clara "frota insuficiente: demanda X >
  capacidade Y" e o botão de calcular fica bloqueado.

### Etapa 3 — Resultado

Ao entrar nesta etapa (botão "Calcular rota"), o sistema resolve e exibe:

- **Mapa interativo** (Folium) ocupando a maior parte da tela, com:
  - marcadores distintos para depósitos e clientes;
  - cada rota desenhada com uma **cor diferente**, seguindo a **geometria real das ruas** (OSRM);
- **Painel de resumo** lateral com:
  - custo total da solução;
  - uma linha por rota: cor, tipo de veículo, depósito de origem, e **carga usada / capacidade**;
  - tempo de solução do solver;
  - status (ótimo / inviável).
- Botão para **voltar** e ajustar parâmetros e recalcular (auditar hipóteses).

## 6. Critérios de aceite do MVP

O MVP está pronto quando, em localhost:

1. O usuário consegue, sem tocar em código, montar um cenário com ≥ 2 depósitos e ≥ 2 tipos de
   veículo e obter uma solução.
2. Endereços em texto são geocodificados; falhas são sinalizadas e corrigíveis.
3. A solução exibida é a do VRPSolverEasy (mesmo resultado que o solver produziria via script).
4. As rotas aparecem no mapa seguindo as ruas, com cores distintas e resumo numérico coerente
   (carga ≤ capacidade em toda rota; soma das demandas atendida).
5. Cenários inviáveis (frota insuficiente, sem depósito) são barrados com mensagem clara, sem crash.
6. Nenhuma chamada a serviço pago; nenhuma chave de API necessária.

## 7. Instância de referência (para validar)

A pasta `../Trabalho_final/` contém uma instância real de farmácias em Niterói-RJ (endereços,
coordenadas em `coordsf.xlsx`, matriz em `dist_matrix_km.xlsx`) e um modelo VRPSolverEasy já
funcionando no `notebook_tf.ipynb`. Configurar o app com **1 depósito + 1 tipo de veículo** sobre
esses pontos deve reproduzir o custo que o notebook calcula hoje — é o teste de regressão do solver.
Veja `REFERENCE.md` para detalhes.
