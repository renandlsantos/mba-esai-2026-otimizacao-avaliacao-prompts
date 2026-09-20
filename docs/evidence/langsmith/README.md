# Evidências LangSmith

Exportação real via API e captura original da interface em 20/09/2026. Estes arquivos são do **histórico anterior**, com juiz `spark/fast` e avaliação parcial. A comparação concluída está em [run-2026-09-20-json-judge](run-2026-09-20-json-judge/README.md); os números da entrega vêm de lá.

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

Os três traces e a captura acima pertencem ao histórico com juiz `spark/fast` e não entram na
comparação final. O [status de pausa](status-pendente-2026-09-20.md) fica preservado como registro
do que foi interrompido; ele foi superado pela
[rodada homogênea](run-2026-09-20-json-judge/README.md), que completou os 15 exemplos de cada
versão sem nenhum julgamento rejeitado.
