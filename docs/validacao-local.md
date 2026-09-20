# Validação local — 2026-09-19

- Python 3.11.16, dependências diretas originais em requirements.txt.
- `.venv/bin/python -m pytest -q`: **35 passed**, 0 falhas.
- `git diff --check`: passou.
- `git diff --exit-code -- src/evaluate.py src/metrics.py src/utils.py datasets/bug_to_user_story.jsonl`: sem diferenças.
- Hashes SHA-256 dos quatro arquivos comparados pelos testes; dataset conserva 15 linhas.
- Seis testes acadêmicos, contratos de pull/push, schema, metadados, falhas externas e runner comparativo cobertos.
- Pull/push usam mocks nos testes. Nenhuma chamada a LangSmith/LLM foi realizada.
- Assinaturas do SDK instalado verificadas: hub.pull/push, Client.update_prompt, evaluate, ExperimentResults.experiment_name e TracerSessionResult.url.

## Diagnósticos durante desenvolvimento

1. Testes iniciais falharam porque v2 e implementação não existiam (fase vermelha do TDD).
2. Busca ingênua por TODO rejeitava a palavra portuguesa “todos”; corrigido com limite de palavra, preservando rejeição do marcador.
3. Identificada lacuna do evaluator upstream: médias ignoram respostas vazias e não há experimento/feedback explícito. Runner complementar reutiliza métricas, publica experimento e exige 15 resultados.

## Dependências e limites

Advisory de revisão Endor recebido. Busca de ferramentas não encontrou dependency-reviewer/package-risk; coordenador confirmou indisponibilidade. Requirements upstream preservado, instalado em venv isolado. **Sem atestado de segurança das dependências**; revisão de versões continua recomendada antes de uso operacional fora do desafio.

## Estado final

Código validado offline. Convergência mantém pendência externa de notas >=0.8, 3–5 iterações, dashboard e três traces. Não foram publicadas transcrições ou credenciais.

## Revisão independente e correção — 2026-09-19
R294-01: o juiz podia responder `{}` e os defaults do starter viravam zero; 14 notas0,9 diluíam a falha numa média0,84 aprovada. Solução em strict_metrics.py preserva bytecode/prompts/fórmulas e usa globals privados para injetar parser estrito antes dos defaults, sem monkey patch no módulo compartilhado.

`rtk proxy .venv/bin/python -m pytest -q`: **54 passed in 0.30s**. Casos novos: objetos incompletos, campos faltantes, tipos inválidos, não finitos, zero legítimo e fórmula F1 original. Revisão independente reproduziu rejeição de `{}`/reasoning-only, três métricas concorrentes sem interferência e quatro hashes congelados intactos. Nenhuma API real foi chamada.
