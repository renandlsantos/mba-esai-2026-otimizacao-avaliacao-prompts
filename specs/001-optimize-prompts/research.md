# Pesquisa e decisões

- Decisão: manter versões upstream e inspecionar assinatura do SDK instalado. Motivo: evaluator já depende dessas APIs; migração de versões é outro escopo. Documentação atual: https://docs.langchain.com/langsmith/manage-prompts-programmatically (consultada 2026-09-19).
- Decisão: system estático via SystemMessage e human template. Motivo: exemplos com chaves literais não devem virar variáveis. Alternativa de escapar todas as chaves é mais frágil.
- Decisão: few-shot com exemplos originais, não retirar respostas do dataset. Motivo: evitar contaminação da avaliação. Role prompting estabelece responsabilidade; formato fixo auxilia clareza.
- Decisão: rejeitar estrutura remota não suportada em vez de truncar mensagens. Motivo: pull deve ser fiel.
- Decisão: testes offline para contratos; LangSmith/modelos são fase externa. Não inferir 0.8 de testes estáticos.

## Materiais consultados
Referências apenas, sem republicar transcrições privadas: Full Cycle Prompt Engineering, aulas 16574 (One e Few-shot e situações críticas), 16616 (System vs User Prompt), 16730 (Fazendo pull e controle de versão). As aulas orientam exemplos coerentes, separar regras de dados e registrar commit/hash remoto em cada avaliação.
