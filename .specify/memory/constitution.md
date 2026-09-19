# Otimização e Avaliação de Prompts Constitution

## Core Principles

### I. Contrato acadêmico preservado
MUST preservar byte a byte src/evaluate.py, src/metrics.py, src/utils.py e datasets/bug_to_user_story.jsonl.

### II. Especificação antes de implementação
MUST rastrear código e testes a requisitos em specs/001-optimize-prompts; revisar cada fase do Spec Kit.

### III. Evidência honesta
MUST distinguir testes offline de avaliações reais. Notas, links e tracing só podem ser registrados após execução real. Aprovação exige cada uma das cinco métricas >= 0.8.

### IV. Segredos e conteúdo privado
MUST manter credenciais fora do Git. Materiais privados do MBA são referências, nunca copiados integralmente ao repositório público.

### V. Simplicidade e falha explícita
MUST manter CLI Python pequeno, validar antes de publicar e retornar status diferente de zero em falhas. Não registrar tokens ou payloads de exceção externa.

## Restrições adicionais
LangChain, LangSmith, YAML, few-shot e role prompting são obrigatórios. O dataset conserva seus 15 exemplos. Os exemplos do prompt serão originais, separados do conjunto de avaliação.

## Desenvolvimento e revisão
Constitution → specify → plan → tasks → implement → converge. Testes automatizados precedem commit. Publicação de prompt e avaliação externa dependem de credenciais configuradas pelo titular; a entrega na plataforma é etapa posterior.

## Governance
Mudanças exigem justificativa em spec e revisão dos testes. Semver: major altera princípios, minor acrescenta regra, patch esclarece texto. Revisão deve verificar as cinco regras e o estado real das evidências.

**Version**: 1.0.0 | **Ratified**: 2026-09-19 | **Last Amended**: 2026-09-19
