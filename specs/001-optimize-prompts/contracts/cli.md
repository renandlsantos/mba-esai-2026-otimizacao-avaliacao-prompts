# Contrato CLI

Executar na raiz do repositório. python src/pull_prompts.py exige LANGSMITH_API_KEY, lê leonanluppi/bug_to_user_story_v1 e grava prompts/bug_to_user_story_v1.yml. Retorno 0 em sucesso, 1 em erro. Arquivo preexistente não é alterado se download ou extração falhar.

python src/push_prompts.py exige LANGSMITH_API_KEY e USERNAME_LANGSMITH_HUB. Lê prompts/bug_to_user_story_v2.yml, valida todos os itens antes de publicar publicamente owner/bug_to_user_story_v2. Retorno 0 em sucesso, 1 em erro. Não publica YAML inválido. Exibe URL de sucesso; erros externos mostram classe, não payload.

python src/evaluate.py mantém contrato upstream. Resultados externos só são evidência após verificar todos os 15 casos e ausência de erro por exemplo.
