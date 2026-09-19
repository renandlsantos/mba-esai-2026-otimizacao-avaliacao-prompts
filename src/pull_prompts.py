"""Baixa o prompt inicial preservando o contrato de mensagens do Hub."""
import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import (
    ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate,
)
from utils import save_yaml, check_env_vars, print_section_header

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / 'prompts/bug_to_user_story_v1.yml'
SOURCE = 'leonanluppi/bug_to_user_story_v1'
load_dotenv(ROOT / '.env')


def extract_prompt(prompt):
    """Rejeita estruturas incompatíveis, sem descartar mensagens silenciosamente."""
    if not isinstance(prompt, ChatPromptTemplate) or len(prompt.messages) != 2:
        raise ValueError('Esperado ChatPromptTemplate com system e human.')
    system, human = prompt.messages
    if not isinstance(system, SystemMessagePromptTemplate) or not isinstance(human, HumanMessagePromptTemplate):
        raise ValueError('Ordem ou tipos de mensagem incompatíveis.')
    if prompt.partial_variables or set(prompt.input_variables) != {'bug_report'}:
        raise ValueError('Contrato deve conter somente bug_report, sem parciais.')
    for message in (system, human):
        if not hasattr(message.prompt, 'template') or message.prompt.template_format != 'f-string':
            raise ValueError('Somente templates textuais f-string são suportados.')
        if not message.prompt.template.strip() or message.prompt.partial_variables:
            raise ValueError('Texto vazio ou variáveis parciais não suportados.')
    return {'bug_to_user_story_v1': {
        'description': 'Prompt inicial obtido do LangSmith Prompt Hub',
        'system_prompt': system.prompt.template,
        'user_prompt': human.prompt.template,
        'version': 'v1',
        'source': SOURCE,
        'source_commit': (prompt.metadata or {}).get('lc_hub_commit_hash'),
        'tags': ['bug-analysis', 'user-story', 'baseline'],
    }}


def pull_prompts_from_langsmith():
    temporary = None
    try:
        prompt = hub.pull(SOURCE, api_key=os.getenv('LANGSMITH_API_KEY'))
        data = extract_prompt(prompt)
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=OUTPUT_PATH.parent, suffix='.tmp', delete=False) as file:
            temporary = Path(file.name)
        if not save_yaml(data, str(temporary)):
            return False
        temporary.replace(OUTPUT_PATH)
        print(f'Prompt salvo: {OUTPUT_PATH.name}')
        return True
    except Exception as error:
        print(f'Falha no pull ({type(error).__name__}). Verifique rede, acesso e contrato do prompt.')
        return False
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    print_section_header('PULL DO PROMPT INICIAL')
    if not check_env_vars(['LANGSMITH_API_KEY']):
        return 1
    return 0 if pull_prompts_from_langsmith() else 1


if __name__ == '__main__':
    sys.exit(main())
