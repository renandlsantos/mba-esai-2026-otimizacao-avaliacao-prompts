# Validação rápida

1. python3.11 -m venv .venv
2. source .venv/bin/activate
3. pip install -r requirements.txt
4. pytest -q
5. cp .env.example .env e configure credenciais, username, projeto exclusivo e modelos disponíveis.
6. python src/pull_prompts.py
7. python src/push_prompts.py (publica o prompt publicamente)
8. python src/evaluate.py

Passos 1–4 são offline após instalação. Passos 6–8 exigem rede e credenciais. Consulte README para comparação v1/v2, captura de evidências e iterações.
