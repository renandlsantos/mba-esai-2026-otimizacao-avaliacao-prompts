# Feature Specification: Otimização e avaliação de prompts

**Feature Branch**: `feature/sdd-fase-294`
**Created**: 2026-09-19
**Status**: Revisada para implementação
**Input**: Fase 294: baixar v1, otimizar com few-shot, publicar v2 e comprovar qualidade com LangSmith.

## User Scenarios & Testing

### User Story 1 - Baixar prompt inicial (Priority: P1)
Como aluno, quero obter o prompt original do Hub sem perder sua estrutura.
**Why this priority**: Estabelecer origem da comparação.
**Independent Test**: Hub simulado retorna mensagens; YAML conserva textos e variável bug_report.
**Acceptance Scenarios**:
1. Given credencial e prompt remoto válidos, When pull, Then salvar v1 no caminho obrigatório.
2. Given erro remoto ou estrutura incompatível, When pull, Then falhar sem substituir arquivo existente.

### User Story 2 - Publicar prompt otimizado (Priority: P1)
Como aluno, quero validar a versão YAML e publicar um template público com metadados.
**Why this priority**: Tornar a solução executável pelo avaliador fornecido.
**Independent Test**: Compilar e renderizar com bug_report, verificar argumentos do cliente simulado.
**Acceptance Scenarios**:
1. Given v2 válida e username configurado, When push, Then publicar owner/bug_to_user_story_v2 público com descrição e técnicas.
2. Given YAML malformado, técnica ausente ou variável estranha, When push, Then não chamar serviço.

### User Story 3 - Comprovar qualidade (Priority: P2)
Como avaliador, quero evidências reais e reprodutíveis de v1 e v2 sobre os 15 casos.
**Why this priority**: Testes estruturais não provam qualidade de respostas.
**Independent Test**: Testes verificam arquivos preservados e checklist; execução externa gera notas reais.
**Acceptance Scenarios**:
1. Given credenciais configuradas, When avaliação, Then registrar notas das cinco métricas e pelo menos 3 traces.
2. Given execução não realizada, When consultar README, Then resultados aparecem como não medidos.

### Edge Cases
Entrada vazia, múltiplos bugs, instruções maliciosas dentro do relato, JSON literal com chaves, rede indisponível, credencial ausente, schema remoto não suportado e falha de gravação.

## Requirements
### Functional Requirements
- **FR-001**: Fazer pull de leonanluppi/bug_to_user_story_v1 e salvar prompts/bug_to_user_story_v1.yml.
- **FR-002**: V2 deve conter persona, regras, 3 exemplos originais, casos limites e separação system/user.
- **FR-003**: Validar YAML e publicar v2 no namespace configurado, público, com tags/descrição/técnicas.
- **FR-004**: Implementar os seis testes acadêmicos e testes de contrato do Hub, sem rede.
- **FR-005**: Preservar os quatro arquivos acadêmicos congelados e os 15 exemplos.
- **FR-006**: Documentar 3–5 iterações reais, comparação v1/v2, screenshots e 3 traces quando disponíveis.
- **FR-007**: Falhar explicitamente sem expor segredos; não fazer publicação durante import ou validação.
### Key Entities
PromptVersion: nome, descrição, system_prompt, user_prompt, version, tags, techniques_applied.
EvaluationEvidence: versão/hash, provedor/modelos, dataset, cinco métricas, link, traces, timestamp.

## Success Criteria
### Measurable Outcomes
- **SC-001**: Os seis testes acadêmicos e testes adicionais passam offline.
- **SC-002**: Cada métrica e a média >= 0.8 em avaliação real de todos os 15 casos.
- **SC-003**: Artefatos congelados continuam idênticos; nenhum segredo no Git.
- **SC-004**: README permite reproduzir pull/push/avaliação e distingue claramente pendências externas.

## Assumptions
O titular configura credenciais e escolhe modelos disponíveis. Não há autorização para procurar segredos. Submissão na plataforma e publicação de prompts aguardam coordenação. O software suporta as dependências fixadas pelo upstream; ambiente recomendado Python 3.11.

## Complemento local Spark (2026-09-20)
Executar 15 exemplos por versão v1/v2 com Spark explícito; preservar prompts e fórmulas congelados. Não substitui LangSmith. Falhas não recebem notas sintéticas; nenhum segredo ou reasoning_content persiste.

## Integração real LangSmith + Spark
Criar experimento ligado ao dataset original de15 casos, com traces reais da geração e dos três julgamentos e cinco feedbacks por caso. Fixar commit Hub quando disponível e verificar equivalência com YAML. Nenhuma aprovação antes de verificar os resultados remotos. Publicação Hubv2 depende de owner confirmado.
