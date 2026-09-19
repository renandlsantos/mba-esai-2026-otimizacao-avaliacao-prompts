# Modelo de dados

YAML contém a chave bug_to_user_story_v2: description, system_prompt e user_prompt são strings não vazias; version deve ser v2; techniques_applied é lista de pelo menos duas strings únicas, incluindo few-shot; tags é lista de strings. system_prompt é estático; user_prompt deve conter exatamente a variável bug_report, sem outras variáveis.

Pull inicial preserva textos system/human do remoto. Estruturas com mensagens extras, multimodalidade ou placeholders não suportados falham explicitamente. Estado: remoto → validado → arquivo; inválido nunca substitui arquivo.

Evidência externa registra data, commit Git, referência/hash do Hub, versões dos modelos, 15 casos processados, cinco scores, média, link e três traces. Valores ausentes são não medidos, nunca zero substituto ou sucesso.
