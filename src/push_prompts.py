"""Valida e publica o prompt v2 publicamente no namespace configurado."""
import os
import re
import sys
from pathlib import Path
from string import Formatter

from dotenv import load_dotenv
from langchain import hub
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client
from utils import load_yaml, check_env_vars, print_section_header

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / 'prompts/bug_to_user_story_v2.yml'
load_dotenv(ROOT / '.env')


def build_prompt(prompt_data):
    """System é texto literal; somente human interpola a variável de entrada."""
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=prompt_data['system_prompt']),
        ('human', prompt_data['user_prompt']),
    ])


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    errors = []
    if not isinstance(prompt_data, dict):
        return False, ['Prompt deve ser um mapping YAML.']
    for field in ('description', 'system_prompt', 'user_prompt', 'version'):
        value = prompt_data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f'{field}: string não vazia obrigatória.')
    if prompt_data.get('version') != 'v2':
        errors.append('version deve ser v2.')
    techniques = prompt_data.get('techniques_applied')
    if not isinstance(techniques, list) or not all(isinstance(x, str) and x.strip() for x in techniques):
        errors.append('techniques_applied deve ser lista de strings.')
    elif len(set(techniques)) < 2 or 'few-shot' not in techniques:
        errors.append('São necessárias duas técnicas distintas, incluindo few-shot.')
    tags = prompt_data.get('tags', [])
    if not isinstance(tags, list) or not all(isinstance(x, str) and x.strip() for x in tags):
        errors.append('tags deve ser lista de strings.')
    system = prompt_data.get('system_prompt', '')
    if isinstance(system, str) and (re.search(r'\bTODO\b', system, re.IGNORECASE) or '{bug_report}' in system):
        errors.append('System não deve conter TODO nem duplicar bug_report.')
    user = prompt_data.get('user_prompt')
    if isinstance(user, str):
        try:
            fields = [(name, fmt, conversion) for _, name, fmt, conversion in Formatter().parse(user) if name is not None]
            if fields != [('bug_report', '', None)]:
                errors.append('user_prompt deve interpolar bug_report exatamente uma vez, sem atributos ou formatação.')
        except ValueError:
            errors.append('user_prompt contém chaves inválidas.')
    return not errors, errors


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    valid, errors = validate_prompt(prompt_data)
    if not valid:
        print('Prompt inválido: ' + '; '.join(errors))
        return False
    username = os.getenv('USERNAME_LANGSMITH_HUB', '').strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', username) or prompt_name != 'bug_to_user_story_v2':
        print('Namespace inválido ou nome diferente de bug_to_user_story_v2.')
        return False
    if not check_env_vars(['LANGSMITH_API_KEY']):
        return False
    identifier = f'{username}/{prompt_name}'
    tags = list(dict.fromkeys(prompt_data.get('tags', []) + prompt_data['techniques_applied']))
    description = prompt_data['description']
    try:
        prompt = build_prompt(prompt_data)
        prompt.metadata = {'version': 'v2', 'techniques_applied': prompt_data['techniques_applied']}
        url = hub.push(identifier, prompt, api_key=os.getenv('LANGSMITH_API_KEY'),
                       new_repo_is_public=True, new_repo_description=description, tags=tags)
        # new_repo_is_public não altera a visibilidade de repositórios já existentes.
        Client(api_key=os.getenv('LANGSMITH_API_KEY')).update_prompt(
            identifier, is_public=True, description=description, tags=tags)
        print(f'Prompt público publicado: {url}')
        return True
    except Exception as error:
        print(f'Falha no push ({type(error).__name__}). Confira acesso e visibilidade no Hub antes de repetir.')
        return False


def main():
    print_section_header('PUSH PÚBLICO DO PROMPT OTIMIZADO')
    if not check_env_vars(['LANGSMITH_API_KEY', 'USERNAME_LANGSMITH_HUB']):
        return 1
    prompts = load_yaml(str(INPUT_PATH))
    if not isinstance(prompts, dict) or set(prompts) != {'bug_to_user_story_v2'}:
        print('YAML deve conter somente bug_to_user_story_v2.')
        return 1
    return 0 if push_prompt_to_langsmith('bug_to_user_story_v2', prompts['bug_to_user_story_v2']) else 1


if __name__ == '__main__':
    sys.exit(main())
