# MBA ESAI 2026 — Otimização e avaliação de prompts

**Preferência do autor:** modelos locais no Spark. Geração e avaliação com `spark/code` (modelo de resposta direta, escolhido para reduzir latência e consumo do orçamento de saída). LangSmith está conectado para registrar experimentos, feedbacks e traces reais.


Implementação da fase 294 do MBA Full Cycle, baseada no [repositório acadêmico](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt).
Transforma relatos de bugs em User Stories, versiona prompts no LangSmith e avalia cinco métricas.

**Estado: código implementado, Hub v2 público e avaliação integral Spark + LangSmith pausada por solicitação do autor; fase 294 pendente, sem merge ou submissão.**
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

**Comparação integral LangSmith pausada e incompleta.** Já existem traces e notas reais; a tabela final só será preenchida após os 15 exemplos de cada versão e conferência remota. A amostra Spark local anterior está documentada separadamente.

| Métrica | v1 | v2 | Critério |
|---|---|---|---|
| Helpfulness | Não medido | Não medido | ≥ 0,8 |
| Correctness | Não medido | Não medido | ≥ 0,8 |
| F1-Score | Não medido | Não medido | ≥ 0,8 |
| Clarity | Não medido | Não medido | ≥ 0,8 |
| Precision | Não medido | Não medido | ≥ 0,8 |
| Média | Não medida | Não medida | ≥ 0,8, sem compensar métrica insuficiente |

Os experimentos e traces autenticados já estão disponíveis. Veja [evidências exportadas](docs/evidence/langsmith/README.md) e [roteiro de evidências e iterações](docs/evidencias.md). Capturas parciais não equivalem à avaliação final; links autenticados não são apresentados como públicos.
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

## Pausa e entrega pendente

A pedido do autor, a fase 294 fica pendente enquanto os demais projetos são submetidos. Foram preservados 4/15 casos v1 com juiz `spark/fast` e, em um experimento separado, 3/15 com juiz `spark/code`. O quarto caso do novo grupo foi rejeitado por JSON inválido; v2 integral ainda não foi executada. O teste pontual de JSON mode passou, mas essa opção ainda não foi implementada nos runners. Veja [estado, evidências e retomada](docs/evidence/langsmith/status-pendente-2026-09-20.md). Suíte atual: 86 testes offline.
