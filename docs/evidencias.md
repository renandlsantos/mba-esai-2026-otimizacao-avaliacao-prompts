# Evidências externas e processo de otimização

## Estado em 2026-09-19

Implementação concluída localmente. Nenhum pull/push real, avaliação de LLM, dashboard compartilhado ou screenshot realizado nesta etapa. O v1 local continua sendo o arquivo original do repositório base.

## Como concluir

1. Configurar credenciais e modelos válidos em `.env` e realizar pull inicial.
2. Executar experimento v1 e guardar o JSON em `results/` para comparação.
3. Publicar v2; executar experimento v2 sobre os mesmos 15 exemplos e modelos.
4. Inspecionar cada falha. Ajustar somente o prompt, mantendo dataset e avaliadores.
5. Repetir 3–5 iterações, anotando hash do prompt, hipótese, mudança e cinco resultados reais.
6. Exigir cada métrica e média >=0,8. Uma geração ou julgamento com erro invalida evidência incompleta.
7. No LangSmith, verificar 15 exemplos, cinco colunas de feedback e pelo menos três traces detalhados.
8. Compartilhar dashboard/screenshot sanitizado e preencher tabela do README com valores reais.

## Registro atual de mudanças

| Etapa | Mudança | Validação | Resultado |
|---|---|---|---|
| Projeto local | Few-shot original, persona, estrutura Markdown e regras de lacunas | Testes estruturais/contratuais offline | Passou; não mede qualidade da LLM |

Não há iterações reais de avaliação a registrar ainda. Os próximos registros devem incluir data,
commit Git, hash remoto, modelos, métricas, erro observado e hipótese. Não preencher com estimativas.

## Limitações do avaliador herdado

O script acadêmico reaproveita dataset remoto pelo nome e agrega somente respostas não vazias.
O runner complementar cria um dataset exclusivo em cada execução e exige todos os 15 resultados.
As funções métricas originais transformam determinadas falhas em zero; isso não significa nota real
válida. O runner rejeita indicação explícita de erro e scores fora de [0,1]. Inspecione também os traces.

A publicação do prompt é pública; dataset e experimentos não são automaticamente compartilhados.
Resultados locais são ignorados pelo Git para evitar publicar conteúdo antes de revisão.
