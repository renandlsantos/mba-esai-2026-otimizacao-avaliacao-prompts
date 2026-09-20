# Fase 294 pendente — pausa solicitada em 20/09/2026

O autor priorizou a submissão dos demais projetos. A fase 294 permanece na branch de desenvolvimento, sem merge nem submissão. Nenhuma avaliação está em execução.

| Histórico | Gerador / juiz | Casos completos | Situação |
|---|---|---:|---|
| LangSmith inicial v1 | spark/code / spark/fast | 4/15 | Preservado; último feedback recuperado após correção da precisão de transporte |
| Novo LangSmith v1 | spark/code / spark/code | 3/15 | Quarto caso rejeitado: terceiro juiz respondeu JSON inválido |
| LangSmith v2 integral | spark/code / spark/code | 0/15 | Ainda não executado |

Esses grupos não são combinados. A amostra local anterior de três casos por versão também não substitui uma avaliação completa no LangSmith.

## Evidências desta rodada

- [Dataset e experimentos públicos do grupo code/code](https://smith.langchain.com/public/ae2782cc-3f91-4ff7-a692-6d11aacd7db9/d): acesso anônimo confirmado por API HTTP200, com 15 exemplos e o experimento parcial. Apenas esse dataset do desafio foi compartilhado.
- [Verificação do compartilhamento](public-code-code-dataset.json).
- [Trace da falha no quarto exemplo](failure-code-code-v1-example04.json): entradas, saídas finais e estado, sem credenciais, cabeçalhos ou configuração de ambiente. Não houve feedback de aprovação para esse exemplo.
- [Diagnóstico JSON mode](json-mode-probe.json): uma chamada já em curso recebeu resposta válida em 2,67s. O parâmetro foi aceito nessa chamada; isso não comprova confiabilidade em todo o dataset.

O modo JSON ainda **não foi integrado aos runners**. Os padrões `spark/code` nos dois papéis e os textos preparados pelo autor foram preservados, com correção das afirmações absolutas sobre determinismo/truncamento. A suíte possui 86 testes offline passando; há regressões para o juiz padrão e rejeição de checkpoint de outro juiz. Os quatro arquivos acadêmicos protegidos permanecem intactos.

## Retomada futura

Revisar a integração explícita de JSON mode no juiz, registrar a configuração e validá-la antes de um lote homogêneo. Mudança de configuração exige novo experimento, sem misturar notas. Depois completar os 15 casos v1/v2, realizar e registrar iterações genuínas do prompt, verificar notas e três traces finais, e obter screenshots finais. Não contar smoke, falhas de transporte ou troca de juiz como iteração de otimização.

O prompt v2 permanece público no Hub no commit já documentado. Ainda não existe demonstração completa de aprovação acadêmica.
