# MBA ESAI 2026 — Otimização e avaliação de prompts

Implementação da fase 294 do MBA Full Cycle, baseada no [repositório acadêmico](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt).
Transforma relatos de bugs em User Stories, versiona prompts no LangSmith e avalia cinco métricas.

**Estado: código e testes locais implementados; avaliação real e aprovação acadêmica pendentes.**
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

## Resultados Finais

**Resultados acadêmicos LangSmith ainda não medidos.** A execução complementar Spark, com credencial explicitamente autorizada, é documentada separadamente abaixo.

| Métrica | v1 | v2 | Critério |
|---|---|---|---|
| Helpfulness | Não medido | Não medido | ≥ 0,8 |
| Correctness | Não medido | Não medido | ≥ 0,8 |
| F1-Score | Não medido | Não medido | ≥ 0,8 |
| Clarity | Não medido | Não medido | ≥ 0,8 |
| Precision | Não medido | Não medido | ≥ 0,8 |
| Média | Não medida | Não medida | ≥ 0,8, sem compensar métrica insuficiente |

Dashboard público e screenshots: ainda não disponíveis. [Roteiro de evidências e iterações](docs/evidencias.md).
A validação offline não substitui estas notas e o projeto ainda não deve ser submetido como aprovado.

## Testes e preservação

Os seis testes exigidos estão em `tests/test_prompts.py`. Os testes adicionais cobrem contrato do
Hub, schema inválido, falha externa sem vazamento, chaves literais, gravação segura, cálculo das
métricas derivadas e recusa de avaliações incompletas.

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

O runner `src/evaluate_spark.py` executa sequencialmente os 15 exemplos congelados para uma versão. Usa `spark/code` para gerar e `spark/fast` para julgar, temperatura 0, 4096 tokens e timeout de 300 s, sem retries automáticos. Lê exclusivamente `~/.config/spark/spark-api.env` via python-dotenv sem interpolação de variáveis (`SPARK_BASE_URL`/`SPARK_API_KEY`, ou aliases `OPENAI_BASE_URL`/`OPENAI_API_KEY`). Não imprime configuração, requests, exceções do provedor ou `reasoning_content`.

```bash
.venv/bin/python src/evaluate_spark.py --version v1 --output results/spark-v1.json
.venv/bin/python src/evaluate_spark.py --version v2 --output results/spark-v2.json
```

Sem `--resume`, o destino não pode existir. Cada exemplo concluído é persistido atomicamente; uma falha deixa `complete:false`, sem médias nem aprovação. As funções originais são compiladas de sua AST em namespace privado, preservando prompts e fórmulas sem executar os imports e `load_dotenv()` dos módulos congelados (que procurariam configurações ancestrais). O parser exige JSON e notas válidas. O relatório registra hashes dos insumos, respostas finais e scores; não armazena raciocínio interno do modelo.

Esta comparação é local e exploratória: não cria experimentos, dashboard ou traces LangSmith e **não satisfaz sozinha a entrega exigida pela plataforma**. O juiz não foi calibrado com avaliadores humanos; as médias são estimativas desse juiz, não uma certificação de qualidade.

Para uma amostra curta, use `--limit 3`. Retome no mesmo arquivo com `--resume` (e opcionalmente novo `--limit`); configuração e hashes devem coincidir. Só exemplos integralmente avaliados são reutilizados. Amostras menores que 15 exemplos não recebem médias nem aprovação. Criar um arquivo `.stop` ao lado do relatório (mesmo nome-base) pausa antes do próximo exemplo; remova-o antes de retomar.

O caminho de credenciais pode ser alterado explicitamente com `--credentials /caminho/spark-api.env`. A retomada requer a mesma versão do runner e do parser estrito além dos hashes registrados. Uma avaliação completa abaixo do limiar retorna exit code 1; uma amostra parcial retorna 0 com `complete:false`, sem aprovação.

### Amostra real de 20/09/2026

Foram executados 3 de 15 exemplos por versão, com `spark/code` e juiz `spark/fast`; os seis casos tiveram JSON válido nas três métricas. A comparação continua incompleta, sem média nem aprovação. Veja [notas por exemplo e limites da evidência](docs/spark-sample-2026-09-20.md). Suíte atual: 69 testes offline, incluindo clone limpo.
