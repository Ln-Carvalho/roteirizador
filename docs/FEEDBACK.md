# Feedback de uso do MVP

> Documento vivo. Cada rodada de teste vira uma seção. Para cada item: **observação original**
> (preservada) + **status** + **o que foi feito**. Itens em aberto ficam na seção mais recente.
>
> **Para o próximo agente:** o app é `roteirizador/app.py` (wizard Streamlit de 3 etapas) sobre os
> módulos em `roteirizador/core/`. Restrições inegociáveis em `roteirizador/CLAUDE.md`
> (100% Python, custo zero, VRPSolverEasy como único solver, sem emojis). Rode os testes com
> `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest -q` e suba o app com
> `streamlit run app.py`. Lições acumuladas em `tasks/lessons.md`.

Legenda de status: **[RESOLVIDO]** · **[PARCIAL]** · **[BACKLOG]** (fora do MVP) · **[ABERTO]**

---

## Rodada 1 — primeiro uso (2026-06-08)

### Etapa 1 (Endereços)

**1. Campo de endereço confuso — sem orientação de preenchimento.**
O usuário não sabe se deve colocar número, rua, bairro etc. Ideal: exemplo de preenchimento;
se possível, autocomplete/validação em tempo real via geocoding para validar e preencher lat/lon.
- **[PARCIAL]** Adicionados `help` na coluna Endereço e captions com exemplo
  (`Rua da Conceicao 100, Centro, Niteroi, RJ`) e dica do botão "+".
- **[BACKLOG]** Autocomplete/validação em tempo real: esbarra no rate-limit do Nominatim
  (1 req/s) — fora do escopo do MVP.

**2. Campo "Demanda" sem explicação.**
Usuário leigo em roteirização não sabe o que é demanda. Ideal: explicação/tooltip com exemplo.
- **[RESOLVIDO]** Tooltip (`help`) explicando demanda como quantidade inteira a entregar.

**3. Demanda não aceitava valor decimal.**
- **[RESOLVIDO — por decisão de projeto]** Demanda e capacidade são **inteiras**, pois o
  VRPSolverEasy exige inteiros (ver item 6). Campo agora é inteiro explícito
  (`NumberColumn(min_value=0, step=1, format="%d")`) com tooltip deixando claro.

**4. Botão "Adicionar ponto" pouco intuitivo — não fica claro que o ponto entra na lista abaixo.**
- **[PARCIAL]** Caption indicando o uso do "+" no fim da tabela. Confirmação visual mais rica
  ainda não implementada.

**5. Erro ao criar ponto novo na lista: `TypeError: bad operand type for unary ~: 'NoneType'`
(app.py:76) + checkbox "Depósito" não aparecia na linha nova.**
- **[RESOLVIDO]** Linha nova do `data_editor` vinha com `None`; o filtro por string deixava a
  linha vazia passar e `~None` estourava. Agora higienizamos os tipos (`fillna`+`astype`) numa
  cópia antes de filtrar; o checkbox passa a renderizar.

### Etapa 2 (Frota)

**6. Ao preencher e dar Tab para a próxima célula, o valor digitado sumia e era preciso digitar
de novo.**
- **[RESOLVIDO]** Causa: reescrever a base do `data_editor` com a saída a cada rerun
  dessincroniza o delta interno do widget. Corrigido com o padrão base-estável + `key` +
  higienização em cópia + snapshot só na navegação.

### Etapa 3 (Resultado)

**7. Capacidade total 1000, demanda 180, Van cap. 500 × 2, custo/km 1.0 → ao calcular:
`Erro no solver: capacity must be an integer`.**
- **[RESOLVIDO]** VRPSolverEasy exige `capacity` e `demand` inteiros. Adicionado
  `int(round(...))` na fronteira do solver (`core/solver.py`) e UI passou a coletar inteiros.

---

## Rodada 2 — novos testes (2026-06-08)

> Itens reportados após as correções da Rodada 1.

### Etapa 1 (Endereços)

**1. Para criar uma nova linha foi preciso clicar duas vezes e preencher duas vezes.**
- **[RESOLVIDO]** Mesma raiz do item 6 da Rodada 1: a base do `data_editor` estava sendo
  reescrita com a saída do editor a cada rerun, dessincronizando o delta interno (a linha
  adicionada virava base **e** permanecia no delta = linha-fantasma). Corrigido nas Etapas 1 e 2
  com o padrão: base estável (nunca reescrita no render) + `key=` + higienização numa cópia +
  snapshot da base apenas nos handlers de navegação.
- **Pendência de verificação:** confirmado que o app sobe (HTTP 200) e os 16 testes passam, mas o
  comportamento de adicionar linha é estado de widget e ainda **não foi validado no navegador**.

---

## Rodada 3 — Melhorias Finais (2026-06-08)

> Fechamento de refinamentos solicitados apos testes do MVP.

### Etapa 2 (Frota)

**1. Permitir Multiplas Viagens por Veiculo (MTVRP)**
O modelo bloqueava o calculo caso a demanda total fosse maior que a capacidade da frota, mas nao considerava que o veiculo poderia fazer multiplas viagens em serie.
- **[RESOLVIDO]** Adicionado um toggle "Permitir multiplas viagens por veiculo". Quando ativado, a restricao de "frota insuficiente" e relaxada, e o VRPSolverEasy recebe um `max_number` expandido, permitindo rotas extras por veiculo.

**2. Validacao de Demanda Individual vs Capacidade (Sem Split Delivery)**
Se apenas um cliente possui demanda superior ao maior veiculo disponivel, a rota e inviavel (nao consideramos entrega dividida).
- **[RESOLVIDO]** Incluida trava: `max(demanda_pontos) <= max(capacidade_frota)`. Caso violada, bloqueia o botao Calcular e avisa que o modelo nao suporta fracionar entrega do cliente.

### Etapa 3 (Resultado)

**3. Custo final exibido em 'km' em vez de unidade monetaria**
A tela final exibia "Custo total: [valor] km", embora a conta fosse o produto Distancia x Custo/KM (ou seja, monetario).
- **[RESOLVIDO]** O card do resumo principal agora exibe `Custo total: R$ {custo_total:.2f}` para ficar claro que e financeiro.

**4. Falta de clareza sobre a Sequencia exata de Enderecos por rota**
As descricoes mostravam apenas IDs e distancia, exigindo analisar a geometria do mapa para descobrir a ordem exata.
- **[RESOLVIDO]** Feito o pareamento ID -> Endereco e inserido o campo **"Sequencia"** no detalhe da rota mostrando a ordem (ex: `Deposito ➔ Cliente 1 ➔ Deposito`).

---

## Novos itens (preencher aqui)

> Adicione abaixo o feedback da proxima rodada de testes. Sugestao de formato por item:
>
> - **Etapa:** (1 / 2 / 3)
> - **O que aconteceu:** descricao do comportamento observado
> - **Esperado:** o que deveria acontecer
> - **Evidencia:** mensagem de erro / passos para reproduzir / print
>
> (area livre)
