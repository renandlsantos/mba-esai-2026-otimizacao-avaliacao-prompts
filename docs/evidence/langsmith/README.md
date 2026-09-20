# Evidências LangSmith

Exportação real via API e captura original da interface em 20/09/2026. **Avaliação parcial; fase 294 pausada por solicitação do autor, sem aprovação final.**

## O que o enunciado exige

README com link público do dashboard, screenshots das avaliações com notas mínimas de 0,8 e tabela comparativa v1/v2. Também exige dataset de 15 casos, tracing detalhado de pelo menos três exemplos e 3–5 iterações. JSONs complementam, mas não substituem os screenshots exigidos.

## Arquivos

- [trace-v1-01.json](trace-v1-01.json) — [registro no LangSmith](https://smith.langchain.com/o/99fa135f-5317-45c0-9795-6b5836b05b44/projects/p/e809e3be-a8cc-4553-b863-80910b701e5f/r/f537bee4-9510-4815-ac57-af5e7a0349b6?poll=true).
- [trace-v1-02.json](trace-v1-02.json) — [registro no LangSmith](https://smith.langchain.com/o/99fa135f-5317-45c0-9795-6b5836b05b44/projects/p/e809e3be-a8cc-4553-b863-80910b701e5f/r/ce8c6c22-8865-48d5-9bbf-526995ba0aeb?poll=true).
- [trace-v1-03.json](trace-v1-03.json) — [registro no LangSmith](https://smith.langchain.com/o/99fa135f-5317-45c0-9795-6b5836b05b44/projects/p/e809e3be-a8cc-4553-b863-80910b701e5f/r/7586c1c4-cae7-4a8e-8ce9-605f2d73d62e?poll=true).
- [Print original do primeiro trace](trace-v1-01-parcial.jpg): geração, três julgamentos e cinco notas deste exemplo.

- [Snapshot da publicação pública v2](hub-v2-publication.json): commit do Hub, hash YAML e equivalência verificada.

## Limites

Links atuais exigem acesso à conta; ainda não foram confirmados como públicos. Não há médias finais nem comparação completa nesta captura. Os arquivos JSON incluem apenas campos de execução, entradas, saídas e notas; não incluem credenciais ou configuração de ambiente. O print captura somente a região do trace, excluindo a barra lateral com dados pessoais; o conteúdo da avaliação não foi alterado.

## Estado após a troca do juiz

Consulte [status pendente e próximos passos](status-pendente-2026-09-20.md). Os três traces e a captura acima pertencem ao histórico com juiz `spark/fast`; o novo grupo `spark/code` tem evidências e falha documentadas separadamente.
