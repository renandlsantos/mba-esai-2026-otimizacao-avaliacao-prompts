# Implementation Plan: Otimização e avaliação de prompts

**Branch**: `feature/sdd-fase-294` | **Date**: 2026-09-19 | **Spec**: [spec.md](spec.md)

## Summary
Implementar CLI de pull/push e prompt v2, mantendo o avaliador original. Usar template de mensagens com system estático e human parametrizado. Testes do Hub usam mocks; avaliações reais permanecem explicitamente pendentes de credenciais.

## Technical Context
**Language/Version**: Python 3.11 (sintaxe compatível com 3.9+).
**Primary Dependencies**: versões upstream de LangChain 0.3.13, core 0.3.28, LangSmith 0.2.7, PyYAML e pytest.
**Storage**: YAML local, Prompt Hub remoto.
**Testing**: pytest sem rede, hashes de integridade e smoke CLI de erro.
**Target Platform**: macOS/Linux.
**Project Type**: CLI.
**Performance Goals**: uma operação de pull/push por invocação; sem serviço residente.
**Constraints**: quatro arquivos acadêmicos imutáveis; sem segredos ou conteúdo de aulas no Git.
**Scale/Scope**: duas versões de um prompt e 15 exemplos de avaliação.

## Constitution Check
Pré e pós design: PASS. Sem alterações nos arquivos congelados, código limitado a scripts e artefatos requeridos. Casos externos distinguem pendência de falha. Sem hooks de extensão configurados.

## Project Structure
- src/pull_prompts.py: extrair exatamente uma mensagem system e uma human sem descartar silenciosamente estruturas desconhecidas; salvar apenas após validar.
- src/push_prompts.py: validação sem rede, construção do template e publicação pública explícita.
- prompts/bug_to_user_story_v2.yml: few-shot + role prompting + estrutura Markdown.
- tests/test_prompts.py: seis critérios acadêmicos; tests/test_hub_workflow.py: contratos, erros, templates e integridade.
- src/evaluate_experiment.py: runner adicional com experimentos/feedback e comparação v1/v2 usando as mesmas funções métricas, sem alterar avaliador original.
- docs/: evidências locais, referências às aulas, roteiro de iterações.
- specs/001-optimize-prompts/: specification, pesquisa, contrato CLI, tarefas e validação.

**Structure Decision**: manter estrutura simples do upstream; não criar framework ou alterar avaliador.

## Complexity Tracking
Sem exceções constitucionais. Avaliação comparativa auxiliar será documentada usando funções públicas do avaliador sem modificar seus arquivos.
