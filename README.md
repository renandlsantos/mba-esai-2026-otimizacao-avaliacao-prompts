# MBA ESAI 2026 — Otimização e avaliação de prompts

**Preferência do autor:** modelos locais no Spark. Geração e avaliação com `spark/code` (modelo de resposta direta, escolhido para reduzir latência e consumo do orçamento de saída). LangSmith está conectado para registrar experimentos, feedbacks e traces reais.


Implementação da fase 294 do MBA Full Cycle, baseada no [repositório acadêmico](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt).
Transforma relatos de bugs em User Stories, versiona prompts no LangSmith e avalia cinco métricas.

**Estado: avaliação integral concluída. Cinco comparações completas de 15 exemplos sobre o mesmo dataset e o mesmo juiz, prompt v2 público no Hub, dataset e experimentos com acesso anônimo verificado, e as cinco métricas da versão entregue acima de 0,8.**
Nenhuma nota, publicação no LangSmith ou screenshot de avaliação foi fabricada.

## Processo SDD

Usamos [GitHub Spec Kit](https://github.com/github/spec-kit), versão 1.0.8, com fluxo
constitution → specify → plan → tasks → implement → converge.

- [Constituição](.specify/memory/constitution.md)
- [Especificação e critérios de aceite](specs/001-optimize-prompts/spec.md)
- [Plano técnico](specs/001-optimize-prompts/plan.md)
- [Tarefas e dependências externas](specs/001-optimize-prompts/tasks.md)
- [Validação local](docs/validacao-local.md)

## Técnicas Aplicadas (Fase 2)

| Técnica | Aplicação | Justificativa |
|---|---|---|
| Few-shot | Três pares originais de entrada/saída: filtro, duplicidade e relato insuficiente com tentativa de desvio | Ensinar padrão consistente e mostrar casos limites sem copiar respostas do dataset |
| Role prompting | Product Manager especializado em bugs e histórias de usuário | Definir responsabilidade, linguagem e foco em resultado verificável |
| Skeleton of Thought | Seções fixas: título, história, contexto, critérios e dúvidas | Estruturar o artefato final sem solicitar exposição de raciocínio interno |

O system contém regras e exemplos estáveis; o human contém somente o relato delimitado.
Não há duplicação de `bug_report`. Texto com instruções hostis permanece dado não confiável.
O prompt não deve inventar causas, prazos ou requisitos ausentes. Essas são instruções de comportamento;
adesão real depende de avaliação, não é uma garantia de segurança apenas por texto.

## Como Executar

Recomendado Python 3.11. O desafio aceita Python 3.9+, mas esta implementação foi validada no 3.11.
As versões diretas em `requirements.txt` foram preservadas do upstream.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
cp .env.example .env
```

Preencha `.env` localmente com `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`,
`USERNAME_LANGSMITH_HUB`, `LLM_PROVIDER`, `LLM_MODEL`, `EVAL_MODEL` e a chave do provedor:
`GOOGLE_API_KEY` com `LLM_PROVIDER=google`, ou `OPENAI_API_KEY` com `LLM_PROVIDER=openai`.
Use um nome de projeto exclusivo e modelos disponíveis na sua conta. Os nomes do `.env.example`
são herdados, não uma garantia de disponibilidade atual. Não commite `.env`.

```bash
python src/pull_prompts.py
python src/push_prompts.py
python src/evaluate.py
```

- Pull consulta `leonanluppi/bug_to_user_story_v1`, preserva as mensagens e o hash disponível do Hub.
  Se o contrato remoto mudar, falha sem sobrescrever o v1 local.
- Push valida v2 e publica **publicamente** `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2`.
  Atualiza visibilidade também quando o prompt já existe. Revise o YAML antes de executar.
- Evaluate é o script acadêmico original. CLI retorna 0 no sucesso e 1 em falha.

### Experimentos comparativos e tracing

O `evaluate.py` original calcula métricas no terminal, mas não usa explicitamente o runner de
experimentos/feedback do LangSmith e pode omitir gerações malsucedidas da média.
Ele permanece intacto por exigência acadêmica. Para obter experimentos com os cinco feedbacks e
exigir os 15 resultados, use o runner complementar, que reutiliza as mesmas funções de `metrics.py`:

```bash
python src/evaluate_experiment.py --version v1
python src/evaluate_experiment.py --version v2
```

Cada execução cria dataset remoto exclusivo com os 15 exemplos originais, publica experimento
com concorrência 1 e salva relatório em `results/` (ignorado pelo Git). O terminal mostra a URL real.
Use `--prompt-ref owner/nome:hash` para fixar uma revisão. O relatório registra hash do Hub, hash do
dataset, modelos, notas e IDs dos 15 runs. Para reprodutibilidade, conserve também o commit Git.
Essas execuções chamam modelos e podem consumir créditos. O dataset acadêmico é enviado ao seu LangSmith.

Abra o dashboard, verifique os 15 casos, publique/compartilhe somente evidências adequadas e capture
pelo menos três traces. Faça entre três e cinco iterações registrando o motivo de cada alteração.

A comparação desta entrega usou `evaluate_langsmith_spark.py`, que faz chamadas reais ao Spark com
tracing explícito. Para que as versões fiquem lado a lado na aba Experiments, a primeira execução
cria o dataset e as seguintes reaproveitam o mesmo `--dataset-id`:

```bash
python src/evaluate_langsmith_spark.py --version v1 --output docs/evidence/.../v1.json
python src/evaluate_langsmith_spark.py --version v2 --output docs/evidence/.../v2-iter1.json \
  --dataset-id <id do relatório v1> --prompt-ref renandlsantos/bug_to_user_story_v2:<commit>
```

O juiz recebe `response_format=json_object`; a geração continua sem restrição de formato, porque é
ela que está sob medição. O contrato fica gravado em `judge_response_format` no relatório, no
metadata do experimento, no feedback e no span, e mudá-lo invalida a retomada de checkpoints — notas
obtidas com contratos diferentes não são somadas.

## Resultados Finais

Cinco avaliações completas de 15 exemplos cada, **todas sobre o mesmo dataset e o mesmo juiz**
(`spark/code` gerando e julgando, com contrato JSON apenas no julgamento). São 300 chamadas
reais, com os cinco feedbacks de cada exemplo conferidos remotamente.

| Métrica | v1 (baseline) | **v2 entregue** | v2 iter. 2 | v2 iter. 3 | v2 iter. 4 | Critério |
|---|---|---|---|---|---|---|
| Helpfulness | 0.899 | 0.880 | 0.867 | 0.710 | 0.848 | ≥ 0,80 |
| Correctness | 0.926 | 0.903 | 0.887 | 0.686 | 0.884 | ≥ 0,80 |
| F1-Score | 0.948 | 0.939 | 0.903 | 0.688 | 0.933 | ≥ 0,80 |
| Clarity | 0.895 | 0.895 | 0.863 | 0.737 | 0.861 | ≥ 0,80 |
| Precision | 0.904 | 0.866 | 0.871 | 0.683 | 0.835 | ≥ 0,80 |
| **Média das cinco** | 0.914 | 0.897 | 0.878 | 0.701 | 0.872 | ≥ 0,80 |

A versão entregue é a da iteração 1, com **as cinco métricas acima de 0,8**. As iterações 2, 3
e 4 testaram hipóteses de melhoria que os dados rejeitaram; a jornada completa, com a análise
que motivou cada uma, está em
[evidências da rodada](docs/evidence/langsmith/run-2026-09-20-json-judge/README.md).

A baseline v1 mantém a melhor média. O relatório não a esconde: a referência do dataset
extrapola o relato por convenção, e o v1 extrapola livremente porque quase não impõe regras.
As restrições que tornam o v2 mais defensável para uso real custam similaridade com essa
referência.

### Links públicos

- [Dataset e experimentos](https://smith.langchain.com/public/ad473fb9-1502-47c5-995c-b5b72c5d2bc2/d) —
  acesso anônimo confirmado por requisição sem credencial: HTTP 200, 15 exemplos e 5 sessões
  ([verificação](docs/evidence/langsmith/run-2026-09-20-json-judge/dataset-publico.json)).
- [Prompt v2 no Hub](https://smith.langchain.com/hub/renandlsantos/bug_to_user_story_v2), público,
  com o histórico das quatro iterações. A versão entregue confere byte a byte com
  `prompts/bug_to_user_story_v2.yml` (SHA-256 `f0bcddb0…`), verificado antes da avaliação.
- Três traces detalhados, cada um com a geração, os três julgamentos e as cinco notas:
  [01](docs/evidence/langsmith/run-2026-09-20-json-judge/trace-v2-01.json) ·
  [02](docs/evidence/langsmith/run-2026-09-20-json-judge/trace-v2-02.json) ·
  [03](docs/evidence/langsmith/run-2026-09-20-json-judge/trace-v2-03.json).

Estes números são de execuções reais e não constituem aprovação acadêmica; a avaliação é da
instituição.

## Testes e preservação

Os seis testes exigidos estão em `tests/test_prompts.py`. A suíte tem 91 testes offline e os
adicionais cobrem contrato do Hub, schema inválido, falha externa sem vazamento, chaves literais,
gravação segura, cálculo das métricas derivadas, recusa de avaliações incompletas e o contrato de
saída do juiz — incluindo a prova de que o modo JSON se aplica somente ao julgamento e de que
trocá-lo invalida checkpoint.

`src/evaluate.py`, `src/metrics.py`, `src/utils.py` e `datasets/bug_to_user_story.jsonl` permanecem
idênticos ao upstream, verificados por SHA-256 em [manifesto](docs/upstream-integrity.json).

## Referências de estudo

Conceitos consultados no acervo privado: aulas 16574 (few-shot), 16616 (system versus user)
e 16730 (pull e controle de versão), disciplina Prompt Engineering. A síntese aplicada está em
[research.md](specs/001-optimize-prompts/research.md); nenhuma transcrição privada foi publicada.
API consultada: [documentação oficial do LangSmith](https://docs.langchain.com/langsmith/manage-prompts-programmatically).
A implementação verifica as assinaturas da versão fixada pelo upstream, que difere da documentação mais recente.

### Correção após revisão independente
O runner complementar valida agora o JSON bruto do juiz em `src/strict_metrics.py` antes dos defaults das métricas originais. `{}` ou uma resposta sem nota/justificativa interrompe a avaliação, em vez de virar zero e ser diluída na média. A nota zero completa continua válida. Os prompts e fórmulas congelados são executados com um parser isolado por chamada; `metrics.py` e os demais arquivos protegidos permanecem intactos. Foram adicionadas 19 regressões; suíte naquela revisão: 54 testes offline. Validação concorrente independente confirmou que os parsers não interferem entre métricas.

## Avaliação complementar local com Spark

O runner `src/evaluate_spark.py` executa sequencialmente os 15 exemplos congelados para uma versão. Usa `spark/code` para gerar e julgar, temperatura 0, 4096 tokens e timeout de 300 s, sem retries automáticos. Lê exclusivamente `~/.config/spark/spark-api.env` via python-dotenv sem interpolação de variáveis (`SPARK_BASE_URL`/`SPARK_API_KEY`, ou aliases `OPENAI_BASE_URL`/`OPENAI_API_KEY`). Não imprime configuração, requests, exceções do provedor ou `reasoning_content`.

> **Troca do juiz (2026-09-20).** O juiz era `spark/fast`, que produz raciocínio intermediário antes da resposta: em um
> caso simples, segundo a medição fornecida pelo autor, gastou 2148 dos 4096 tokens (7267 caracteres de raciocínio), o que arrisca `finish_reason=length` e derruba
> a execução. `spark/code` responde direto. Medição lado a lado no mesmo caso (as três métricas): **12,0 s contra 88,2 s**,
> e, nessa amostra fornecida pelo autor, notas mais severas — f1 0,800 vs 0,857 · clarity 0,850 vs 0,910 · precision 0,830 vs 0,970.
> **Consequência metodológica:** resultados medidos com o juiz anterior não são comparáveis com os novos; para comparar
> versões de prompt, reexecute todas elas com o mesmo juiz.

```bash
.venv/bin/python src/evaluate_spark.py --version v1 --output results/spark-v1.json
.venv/bin/python src/evaluate_spark.py --version v2 --output results/spark-v2.json
```

Sem `--resume`, o destino não pode existir. Cada exemplo concluído é persistido atomicamente; uma falha deixa `complete:false`, sem médias nem aprovação. As funções originais são compiladas de sua AST em namespace privado, preservando prompts e fórmulas sem executar os imports e `load_dotenv()` dos módulos congelados (que procurariam configurações ancestrais). O parser exige JSON e notas válidas. O relatório registra hashes dos insumos, respostas finais e scores; não armazena raciocínio interno do modelo.

Esta comparação é local e exploratória: não cria experimentos, dashboard ou traces LangSmith e **não satisfaz sozinha a entrega exigida pela plataforma**. O juiz não foi calibrado com avaliadores humanos; as médias são estimativas desse juiz, não uma certificação de qualidade.

Para uma amostra curta, use `--limit 3`. Retome no mesmo arquivo com `--resume` (e opcionalmente novo `--limit`); configuração e hashes devem coincidir. Só exemplos integralmente avaliados são reutilizados. Amostras menores que 15 exemplos não recebem médias nem aprovação. Criar um arquivo `.stop` ao lado do relatório (mesmo nome-base) pausa antes do próximo exemplo; remova-o antes de retomar.

O caminho de credenciais pode ser alterado explicitamente com `--credentials /caminho/spark-api.env`. A retomada requer a mesma versão do runner e do parser estrito além dos hashes registrados. Uma avaliação completa abaixo do limiar retorna exit code 1; uma amostra parcial retorna 0 com `complete:false`, sem aprovação.

### Amostra real de 20/09/2026

Foram executados 3 de 15 exemplos por versão, com `spark/code` e juiz `spark/fast` (o juiz passou a ser `spark/code` em 2026-09-20); os seis casos tiveram JSON válido nas três métricas. A comparação continua incompleta, sem média nem aprovação. Veja [notas por exemplo e limites da evidência](docs/spark-sample-2026-09-20.md). Suíte naquela etapa: 69 testes offline, incluindo clone limpo.


[Configuração e execução LangSmith mantendo modelos Spark](docs/configurar-langsmith.md).

## Integração real Spark + LangSmith

O runner `src/evaluate_langsmith_spark.py` cria experimentos com o dataset congelado, traces reais da geração e dos três julgamentos e cinco feedbacks por exemplo. Reutiliza `score_answer`, verifica os resultados remotos e suporta retomada estrita. A [documentação de execução](docs/configurar-langsmith.md) explica os arquivos de configuração, o dataset compartilhado e os links: os experimentos ficam separados do projeto-base `MBA-ESAI`. O prompt v2 já está público no handle `renandlsantos`, commit `332d800a16061a89ba3c9f897c3b7ef353aca9822efd77a179f2098f0f88ed56`.

Temperatura 0 não garante determinismo absoluto, e o limite de 4096 tokens ainda permite respostas truncadas, que o runner rejeita. Usar o mesmo modelo como gerador e juiz pode introduzir preferência pelas próprias respostas; não houve calibração humana do juiz. A escolha `spark/code` em ambos os papéis é explícita do autor.

## Estado da entrega

A pausa de 20/09/2026 foi encerrada. O julgamento passou a usar contrato JSON, o que eliminou
a rejeição que interrompia as avaliações, e as cinco comparações completas foram executadas
sobre o mesmo dataset e o mesmo juiz.

Entregue: prompt v2 público no Hub, dataset e experimentos com acesso anônimo verificado,
cinco métricas acima de 0,8 na versão entregue, tabela comparativa, três traces detalhados e
quatro iterações documentadas com hipótese, mudança e resultado — incluindo as que os dados
rejeitaram. Suíte de 91 testes offline; `evaluate.py`, `metrics.py`, `utils.py` e o dataset
permanecem idênticos ao upstream.

Ressalva mantida: a geração e o julgamento usam o gateway Spark, não o Gemini sugerido no
enunciado. O desvio está declarado desde a primeira versão deste README e vale para todas as
versões comparadas, o que preserva a comparação entre elas.
