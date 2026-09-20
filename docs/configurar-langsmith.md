# LangSmith com modelos Spark

A geração e o julgamento continuam no Spark. LangSmith registra Hub, dataset, experimentos, cinco métricas e traces reais. A implementação específica está em `src/evaluate_langsmith_spark.py`; o runner local `evaluate_spark.py` permanece disponível sem publicação de traces.

## Configuração explícita

Guardar a chave LangSmith em `~/.config/langsmith/mba-esai.env`, fora do Git, com permissão 600. O runner lê esse arquivo via python-dotenv sem interpolar variáveis e sem procurar `.env` em diretórios ancestrais. Campos obrigatórios: `LANGSMITH_API_KEY`, `LANGSMITH_ENDPOINT` e `LANGSMITH_PROJECT`. Nesta execução, endpoint `https://api.smith.langchain.com` e projeto-base `MBA-ESAI`.

A configuração Spark continua separada em `~/.config/spark/spark-api.env`, com `SPARK_BASE_URL` e `SPARK_API_KEY` (ou aliases `OPENAI_BASE_URL` e `OPENAI_API_KEY`). Não há necessidade de credencial de modelo em nuvem.

O handle público do workspace foi confirmado como `renandlsantos`. O Hub moderno aceita a chave LangSmith; um token legado separado do Hub não é necessário. O prompt v2 foi publicado com visibilidade pública e equivalência de conteúdo verificada nos 15 exemplos.

## Execução e retomada

```bash
.venv/bin/python src/evaluate_langsmith_spark.py --version v1 --output results/langsmith-v1.json
```

Para v2, informar `--prompt-ref` com o commit publicado e `--dataset-id` com o ID do relatório v1. Assim os dois experimentos compartilham exatamente o mesmo dataset. A opção `--limit 1` permite smoke; `--resume` reutiliza somente exemplos completos com insumos, configuração, hash do runner, dataset e feedbacks remotos verificados. Criar um arquivo `.stop` de mesmo nome-base do relatório pausa antes do próximo exemplo.

O runner usa `spark/code` e juiz `spark/fast`, temperatura 0, 4096 tokens, timeout de 300 s e concorrência 1. Registra um trace raiz por exemplo, um filho LLM da geração e três filhos LLM dos julgamentos; nenhum `reasoning_content` é armazenado. As cinco notas são os três scores acadêmicos e as duas médias derivadas originais, sem alterar os arquivos congelados.

## Onde localizar os resultados

O projeto-base `MBA-ESAI` pode ficar vazio: cada avaliação cria um **experimento separado**, cujo nome começa com `MBA-ESAI-Spark-`. Isso permite associar o projeto de execução ao dataset e comparar versões. O relatório JSON guarda `dashboard_url`, `dataset_id`, `experiment_name` e três links de traces verificados. Use esses links ou a área **Datasets & Experiments** do LangSmith.

- [Dataset compartilhado desta avaliação](https://smith.langchain.com/o/99fa135f-5317-45c0-9795-6b5836b05b44/datasets/afa14990-6b25-46f7-a7db-f38b39e039b1).
- [Experimento v1](https://smith.langchain.com/o/99fa135f-5317-45c0-9795-6b5836b05b44/projects/p/e809e3be-a8cc-4553-b863-80910b701e5f).
- [Prompt v2 público, commit fixado](https://smith.langchain.com/prompts/bug_to_user_story_v2/332d800a?organizationId=99fa135f-5317-45c0-9795-6b5836b05b44).

## Compatibilidade e critérios pendentes

As dependências acadêmicas continuam fixadas, incluindo LangSmith 0.2.7. A interface exibiu aviso sobre dois endpoints depreciados com prazo em 31/01/2027; os endpoints específicos não foram identificados no aviso observado. A execução atual é verificada pela API; a compatibilidade futura exige revisão própria, sem atualizar arbitrariamente a base congelada.

Uma execução completa exige 15 exemplos, feedbacks remotos correspondentes e três árvores de trace completas. Amostra parcial nunca recebe média nem aprovação. `academic_acceptance` continua falso enquanto o conjunto integral de requisitos, incluindo histórico real de iterações, não estiver demonstrado. Smoke ou repetição operacional não são contabilizados como novas iterações de otimização.
