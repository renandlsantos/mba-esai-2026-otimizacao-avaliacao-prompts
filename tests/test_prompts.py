"""Seis critérios acadêmicos para a versão otimizada."""
from pathlib import Path
import yaml
import re

ROOT = Path(__file__).resolve().parents[1]

def prompt():
    return yaml.safe_load((ROOT / 'prompts/bug_to_user_story_v2.yml').read_text())['bug_to_user_story_v2']

def test_prompt_has_system_prompt():
    assert prompt()['system_prompt'].strip()

def test_prompt_has_role_definition():
    assert 'Você é um Product Manager' in prompt()['system_prompt']

def test_prompt_mentions_format():
    assert 'Markdown' in prompt()['system_prompt']
    assert 'Como' in prompt()['system_prompt'] and 'quero' in prompt()['system_prompt']

def test_prompt_has_few_shot_examples():
    text = prompt()['system_prompt']
    assert text.count('Entrada:') >= 3
    assert text.count('Saída:') >= 3

def test_prompt_no_todos():
    assert not re.search(r'\bTODO\b', str(prompt()), re.IGNORECASE)

def test_minimum_techniques():
    techniques = prompt()['techniques_applied']
    assert len(set(techniques)) >= 2
    assert 'few-shot' in techniques
