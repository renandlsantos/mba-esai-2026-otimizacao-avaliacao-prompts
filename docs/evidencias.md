# Evidências externas e processo de otimização

## Estado em 2026-09-20

O prompt v1 foi consultado no Hub e seu commit `2950c33dbd7ffaed2e440b50adfd7769d183f90faf0bae5aa4864354f88e4073` confere com as mensagens do YAML local. A v2 foi publicada como `renandlsantos/bug_to_user_story_v2`, commit `332d800a16061a89ba3c9f897c3b7ef353aca9822efd77a179f2098f0f88ed56`, com visibilidade pública e equivalência conferida nos 15 exemplos.

A amostra local anterior (3 casos por versão) não tinha LangSmith. A rodada atual usa **chamadas reais Spark com traces e feedbacks reais no LangSmith**. Os experimentos estão separados do projeto-base `MBA-ESAI`; o dataset contém os 15 exemplos originais. Os links e a configuração estão em [configurar-langsmith.md](configurar-langsmith.md).

A avaliação integral foi concluída em 20/09/2026, depois que o contrato JSON no juiz eliminou as rejeições de julgamento. Cinco comparações completas de 15 exemplos estão em [run-2026-09-20-json-judge](evidence/langsmith/README.md). O material anterior, parcial e com outro juiz, segue identificado como histórico.

## Critérios da entrega

1. Executar v1 e v2 sobre os mesmos 15 exemplos, com configuração de modelos constante.
2. Confirmar cinco feedbacks por exemplo e pelo menos três traces com geração e julgamentos reais.
3. Inspecionar métricas baixas; se necessário, ajustar somente o prompt, publicar nova versão e avaliar novamente.
4. Registrar cada iteração realmente feita (o enunciado espera 3–5), com hipótese, alteração, hash e notas. Smoke, retomada e repetição técnica não contam como otimização.
5. Exigir cada uma das cinco métricas e sua média >=0,8; não compensar uma métrica insuficiente com outra alta.
6. Publicar tabela comparativa real e screenshots das avaliações finais, mostrando dataset de 15 exemplos e traces detalhados de ao menos três exemplos. Link autenticado sozinho não deve ser chamado de público.

## Registro atual

| Etapa | Mudança | Validação | Resultado |
|---|---|---|---|
| Construção v2 (iteração 1) | Few-shot, persona, estrutura Markdown e regras de lacunas | 15 exemplos no LangSmith | 0,897 — versão entregue, cinco métricas acima de 0,8 |
| Iteração 2 | Critérios ancorados no relato, dúvidas restritas, contexto em uma frase | 15 exemplos | 0,878 — hipótese rejeitada |
| Iteração 3 | Formato da referência, sem seções extras | 15 exemplos | 0,701 — hipótese rejeitada; perdeu a regra de múltiplos defeitos e recusou três relatos |
| Iteração 4 | Cobertura ampliada sobre a iteração 1 | 15 exemplos | 0,872 — hipótese rejeitada |
| Troca do gerador | `spark/best`, `spark/reason` e `spark/glm` no lugar de `spark/code` | 2 casos difíceis, mesmo juiz | Abaixo da baseline; nenhuma métrica da entrega vem daqui |

Detalhamento de cada hipótese em [evidências da rodada](evidence/langsmith/run-2026-09-20-json-judge/README.md).

## Integridade e retomada

`evaluate_langsmith_spark.py` compõe o modelo Spark e reutiliza o mesmo `score_answer`; não duplica fórmulas. Preserva `evaluate.py`, `metrics.py`, `utils.py` e o JSONL original. O checkpoint exige insumos/configuração idênticos, hash do runner, notas finitas e completas, índices coerentes, run IDs únicos e dataset/feedbacks remotos correspondentes.

O smoke inicial antecedeu o campo de hash do runner. Foi arquivado byte a byte antes de uma adoção explícita, com SHA256 do relatório original e `original_runner_sha256:null` — não foi inventada identidade da fonte anterior. O resultado real já completo foi preservado após checagem remota; os casos seguintes registram a versão atual do runner. Essa migração não representa uma iteração de otimização.

A publicação do prompt é pública; dataset, projetos e traces não se tornam públicos automaticamente. Resultados brutos ficam ignorados pelo Git. Os artefatos selecionados para a pasta de evidências são revisados para excluir credenciais, metadados de ambiente e `reasoning_content`.

## Contrato de saída do juiz (retomada de 20/09/2026)

A rodada anterior parou no quarto exemplo porque o juiz devolveu JSON inválido. Os prompts congelados de `metrics.py` já exigem "APENAS um objeto JSON válido", então o contrato passou a ser imposto no transporte: o juiz é instanciado com `json_mode=True` e envia `response_format={"type": "json_object"}`. **A geração não foi alterada** — o prompt sob medição continua com o contrato livre, porque restringir o gerador mudaria justamente o objeto do experimento.

Um teste real com o prompt congelado de clareza confirmou resposta válida em 4,35s antes do lote. O contrato ficou registrado em quatro lugares: `judge_response_format` no relatório local, no metadata do experimento, em `source_info` de cada feedback e no span do juiz no LangSmith. Como o metadata entra na comparação de retomada e o hash de `evaluate_spark.py` mudou, os checkpoints anteriores (4/15 com `spark/fast` e 3/15 sem JSON mode) são recusados automaticamente: notas de juízes com contratos diferentes não se misturam.

**Isto não é uma iteração de otimização de prompt.** É correção de transporte do instrumento de medição, como o arredondamento de quatro casas decimais descrito adiante. Commit `4383e1f`; a suíte passou de 86 para 91 testes offline, sendo os cinco novos dedicados a provar que apenas o juiz recebe o contrato e que trocá-lo invalida checkpoint.

## Precisão de transporte das notas

A API LangSmith rejeitou um feedback com HTTP422 porque a fórmula original produziu `0.9872000000000001` e o endpoint aceita no máximo quatro casas decimais. A correção arredonda somente a nota serializada para a API; o valor bruto permanece no checkpoint e em `source_info.raw_metric_score`. Médias acadêmicas usam os valores brutos. A verificação remota compara a representação de quatro casas. O caso afetado foi recuperado a partir das saídas reais já registradas dos juízes, sem repetir inferência.

Uma alteração do runner invalida a retomada normal. A opção explícita `--adopt-runner-upgrade` exige arquivo fonte anterior com SHA256 comprovado, arquiva o checkpoint anterior sem sobrescrevê-lo e registra a migração após validar os resultados remotos. Não é uma nova iteração de prompt.

Estado detalhado após a troca explícita do juiz: [status pendente](evidence/langsmith/status-pendente-2026-09-20.md).
