# Amostra real Spark — 2026-09-20

Status: **incompleta**, sem aprovação local ou acadêmica. Executados os primeiros 3 de 15 exemplos de cada versão; nenhuma iteração de otimização adicional. Gerador `spark/code`, juiz `spark/fast`, temperatura 0, 4096 tokens, timeout 300 s, concorrência 1. Três julgamentos por resposta com as funções, prompts e fórmulas originais congeladas. Não houve fallback de juiz.

| Versão | Exemplo | F1 | Clareza | Precisão | Helpfulness | Correctness |
|---|---:|---:|---:|---:|---:|---:|
| v1 | 1 | 0.8972 | 0.9500 | 1.0000 | 0.9750 | 0.9486 |
| v1 | 2 | 0.9474 | 0.9500 | 1.0000 | 0.9750 | 0.9737 |
| v1 | 3 | 1.0000 | 0.9500 | 1.0000 | 0.9750 | 1.0000 |
| v2 | 1 | 0.9744 | 0.9100 | 1.0000 | 0.9550 | 0.9872 |
| v2 | 2 | 0.8686 | 0.9400 | 1.0000 | 0.9700 | 0.9343 |
| v2 | 3 | 1.0000 | 0.9750 | 1.0000 | 0.9875 | 1.0000 |

Não calculamos média de aprovação para amostras incompletas. Esses resultados não demonstram desempenho nos outros 12 exemplos, não calibram o juiz com avaliação humana e não substituem dashboard/traces/experimentos LangSmith.

A execução piloto v1 foi pausada com SIGTERM após persistir o terceiro caso, conforme coordenação; uma eventual chamada seguinte foi descartada integralmente. A execução v2 terminou normalmente com `--limit 3`. O problema de descoberta implícita de `.env` ancestral foi corrigido isolando a compilação das funções originais, sem importar os módulos congelados. O runner atual lê apenas o arquivo de credenciais explícito, sem interpolação.

## Retomada

Usar a mesma versão do runner/parser e os mesmos arquivos de checkpoint. Os hashes de prompt, dataset e métricas são verificados. Exemplos parcialmente gerados/avaliados não são reutilizados.

```bash
.venv/bin/python src/evaluate_spark.py --version v1 --output results/spark-2026-09-20-v1.json --resume
.venv/bin/python src/evaluate_spark.py --version v2 --output results/spark-2026-09-20-v2.json --resume
```

A retomada completa depende da coordenação da próxima rodada. Os checkpoints ficam no acervo local do MBA, não no repositório público.

## Validação do software

- 69 testes offline passaram no repositório e em clone limpo do commit `ac4b3ea`, usando o ambiente de dependências já instalado.
- `git diff --check`: passou.
- Arquivos protegidos sem diferenças contra `upstream/main`.
- Credenciais, requests brutos e `reasoning_content` não foram incluídos nas evidências.
