# Tasks: Otimização e avaliação de prompts

## Phase 1: Setup
- [X] T001 Registrar constituição e especificação em .specify/memory/constitution.md e specs/001-optimize-prompts/spec.md.
- [X] T002 Preparar ambiente Python com requirements.txt upstream e documentar decisões em research.md.

## Phase 2: Foundational
- [X] T003 Registrar hashes dos arquivos congelados em docs/upstream-integrity.json e proteger .venv/.env em .gitignore.
- [X] T004 Criar testes offline de contratos em tests/test_hub_workflow.py.

## Phase 3: US1 — Pull (MVP)
- [X] T005 [US1] Implementar extração fiel e falhas sem sobrescrita em src/pull_prompts.py; validar pelo teste de download simulado.

## Phase 4: US2 — Otimizar e publicar
- [X] T006 [P] [US2] Implementar os seis testes acadêmicos em tests/test_prompts.py.
- [X] T007 [US2] Criar prompts/bug_to_user_story_v2.yml com 3 exemplos originais e regras de edge cases.
- [X] T008 [US2] Implementar validação de schema e publicação pública em src/push_prompts.py, com teste de argumentos e falhas.

## Phase 5: US3 — Evidências
- [X] T009 [US3] Documentar roteiro de avaliação comparativa, iterações e limitações upstream em README.md e docs/evidencias.md.
- [ ] T010 [US3] Executar pull/push reais, 3–5 iterações sobre 15 exemplos, registrar cinco métricas >=0.8, dashboard e 3 traces em docs/evidencias.md. Dependência externa: credenciais e autorização coordenada.

- [X] T013 [US3] Implementar runner complementar em src/evaluate_experiment.py e contratos offline em tests/test_experiment.py para publicar experimentos e comparar v1/v2 com métricas originais.

## Phase 6: Polish
- [X] T011 Executar pytest, revisar diff/segredos/integridade e registrar resultado em docs/validacao-local.md.
- [X] T012 Executar converge e registrar pendências externas em tasks.md.

## Dependencies and parallel execution
T001→T002→T003/T004→T005; T006 pode ocorrer junto de T005 porque usa outro arquivo. T007→T008. T009 após T005/T008. T010 só com credenciais. T011/T012 consolidam tudo.

## Implementation strategy
MVP: pull sem perda de dados. Depois v2 e push com testes. Por último evidências reais sem confundir validação estrutural com notas da LLM.

## Phase 7: Convergence

- [ ] T014 [US3] Concluir evidências externas de FR-006/SC-002/US3-AC1 em docs/evidencias.md e README.md após configuração de credenciais: métricas reais, 3–5 iterações, dashboard e três traces (partial; operacional, relacionado a T010).

### Revisão de convergência em 2026-09-19

7 requisitos funcionais, 4 critérios de sucesso, 6 cenários de aceite, decisões do plano e 5 princípios constitucionais revisados. Um achado HIGH/partial: falta evidência externa de avaliação. Nenhuma violação dos arquivos congelados. Código e testes offline completos; entrega acadêmica não declarada concluída. T010/T014 dependem de credenciais, não de implementação pendente.
