# Rodada homogênea de 20/09/2026 — juiz com contrato JSON

Todos os experimentos desta pasta usam a mesma configuração: `spark/code` gerando e julgando,
temperatura 0, `max_tokens` 4096, concorrência 1 e `response_format=json_object` **apenas no
juiz**. Todos avaliam o mesmo dataset de 15 exemplos originais
(`e76d86a5-6445-4b3c-8519-69f125650979`), o que permite comparar as versões lado a lado na
aba Experiments do LangSmith.

A rodada anterior foi interrompida no quarto exemplo porque o juiz devolveu JSON inválido.
Com o contrato imposto no transporte, as avaliações desta pasta rodaram sem nenhum
julgamento rejeitado.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `v1.json` | Baseline: prompt original do Hub (`leonanluppi/bug_to_user_story_v1`). |
| `v2-iter1.json` | Prompt v2 como estava antes desta rodada (Hub `332d800a`). |
| `v2-iter2.json` | Iteração 2 (Hub `373f916c`). |
| `v2-iter3.json` | Iteração 3 (Hub `10109fda`). |

Cada relatório traz metadata com hashes dos insumos, `judge_response_format`, os 15 exemplos
com respostas e notas, as médias, os IDs de execução e as URLs de três traces verificados
remotamente. Os `.log` registram apenas progresso, sem credenciais.

## Jornada de otimização

O enunciado pede que as métricas baixas sejam analisadas e o prompt ajustado em seguida.
Cada iteração abaixo nasceu de um número observado na iteração anterior, não de suposição.

### Iteração 1 — ponto de partida

Prompt v2 com persona de Product Manager, few-shot de três exemplos e saída em cinco seções
(Título, User Story, Contexto, Critérios de aceitação, Dúvidas a esclarecer).

**Resultado:** todas as métricas acima de 0,8, mas abaixo do v1 em quatro das cinco. A
precision foi a mais distante (0,866 contra 0,904).

**Análise:** no exemplo 4, o v2 produziu 1.231 caracteres contra 447 da referência. Criou
critérios sobre filtros, ordenação e lista vazia, que o relato não menciona, e enviou para
"Dúvidas a esclarecer" justamente o que a referência trata como critério.

### Iteração 2 — restringir a especulação

**Hipótese:** se o excesso de conteúdo fora da referência derruba a precision, proibir
critérios não ancorados no relato deve recuperá-la.

**Mudança:** critérios obrigatoriamente ancorados no relato; "Dúvidas" apenas quando impedem
escrever um critério; contexto em uma frase. Os critérios dos exemplos few-shot foram
reescritos, porque demonstravam exatamente os cenários hipotéticos que a nova regra proíbe —
em few-shot, a demonstração costuma pesar mais que a instrução.

**Resultado:** precision subiu 0,005, f1_score caiu 0,036 e a média piorou. **Hipótese
rejeitada.**

**Análise:** a referência do dataset extrapola o relato por convenção. No exemplo 4 ela cita
administrador, tempo real e status "ativo", nenhum deles presente no texto do bug. Proibir a
extrapolação aumenta a aderência ao relato e reduz a cobertura da referência, que é o que o
recall mede.

### Iteração 3 — adotar o formato da referência

**Hipótese:** parte da perda de precision vem das seções que a referência não tem. Se a saída
passar a ter apenas User Story e Critérios de Aceitação, sobra menos texto fora do esperado.

**Mudança:** formato reduzido a `**User Story:**` e `**Critérios de Aceitação:**` em
Dado/Quando/Então, convenção de domínio permitida de volta, proibição explícita de citar
filtros, ordenação, exportação, relatório e permissão quando o relato não os usa. Few-shot e
role-prompting preservados, com os exemplos reescritos no formato novo.

**Resultado:** melhor que as iterações 1 e 2 em precision, helpfulness e correctness.
