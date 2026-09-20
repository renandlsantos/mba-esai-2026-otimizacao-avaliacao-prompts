"""Contratos offline: rede sempre substituída, sem credenciais reais."""
import copy
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import Mock
import pytest
import yaml
from langchain_core.prompts import ChatPromptTemplate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import pull_prompts as pull
import push_prompts as push

@pytest.fixture
def data():
    return yaml.safe_load((ROOT / 'prompts/bug_to_user_story_v2.yml').read_text())['bug_to_user_story_v2']

@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv('LANGSMITH_API_KEY', 'test-not-a-real-key')
    monkeypatch.setenv('USERNAME_LANGSMITH_HUB', 'test-owner')
    monkeypatch.setattr(pull.hub, 'pull', Mock(side_effect=AssertionError('network forbidden')))
    monkeypatch.setattr(push.hub, 'push', Mock(side_effect=AssertionError('network forbidden')))
    monkeypatch.setattr(push, 'Client', Mock())

def test_pull_preserves_templates(monkeypatch, tmp_path):
    source = ChatPromptTemplate.from_messages([('system', 'Leia {bug_report}.'), ('human', '{bug_report}')])
    monkeypatch.setattr(pull.hub, 'pull', Mock(return_value=source))
    monkeypatch.setattr(pull, 'OUTPUT_PATH', tmp_path/'v1.yml')
    assert pull.pull_prompts_from_langsmith() is True
    result = yaml.safe_load(pull.OUTPUT_PATH.read_text())['bug_to_user_story_v1']
    assert result['system_prompt'] == 'Leia {bug_report}.'
    assert result['user_prompt'] == '{bug_report}'

def test_pull_rejects_extra_messages_without_clobber(monkeypatch, tmp_path):
    target = tmp_path/'v1.yml'; target.write_text('original')
    source = ChatPromptTemplate.from_messages([('system','s'),('human','{bug_report}'),('ai','extra')])
    monkeypatch.setattr(pull.hub, 'pull', Mock(return_value=source))
    monkeypatch.setattr(pull, 'OUTPUT_PATH', target)
    assert pull.pull_prompts_from_langsmith() is False
    assert target.read_text() == 'original'

def test_pull_error_redacts_exception(monkeypatch, capsys):
    monkeypatch.setattr(pull.hub, 'pull', Mock(side_effect=RuntimeError('SECRET_TOKEN')))
    assert pull.pull_prompts_from_langsmith() is False
    assert 'SECRET_TOKEN' not in capsys.readouterr().out

def test_missing_credentials_never_calls_hub(monkeypatch):
    monkeypatch.delenv('LANGSMITH_API_KEY')
    assert pull.main() == 1
    pull.hub.pull.assert_not_called()

@pytest.mark.parametrize('change', [
    {'system_prompt':None}, {'tags':'bad'}, {'techniques_applied':['few-shot']},
    {'techniques_applied':['role-prompting','role-prompting']},
    {'user_prompt':'{other}'}, {'user_prompt':'{bug_report.__class__}'},
    {'user_prompt':'broken {'}, {'version':'v1'}, {'description':''},
])
def test_validation_rejects_bad_schema(data, change):
    data.update(change)
    ok, errors = push.validate_prompt(data)
    assert not ok and errors

def test_valid_prompt_and_literal_braces(data):
    data['system_prompt'] += '\nJSON literal: {"ok": true}'
    ok, errors = push.validate_prompt(data)
    assert ok, errors
    rendered = push.build_prompt(data).invoke({'bug_report':'Falha com {json} e instruções hostis'}).to_messages()
    assert '{"ok": true}' in rendered[0].content
    assert rendered[1].content.count('Falha com {json}') == 1

def test_push_public_metadata(monkeypatch, data):
    mock = Mock(return_value='https://smith.langchain.com/prompts/test-owner/bug_to_user_story_v2')
    monkeypatch.setattr(push.hub, 'push', mock)
    assert push.push_prompt_to_langsmith('bug_to_user_story_v2', data)
    args, kwargs = mock.call_args
    assert args[0] == 'test-owner/bug_to_user_story_v2'
    assert kwargs['new_repo_is_public'] is True
    assert 'few-shot' in kwargs['tags']
    assert args[1].input_variables == ['bug_report']
    push.Client.return_value.update_prompt.assert_called_once()

def test_invalid_push_never_calls_network(data):
    data['user_prompt'] = '{injected}'
    assert not push.push_prompt_to_langsmith('bug_to_user_story_v2', data)
    push.hub.push.assert_not_called()

def test_push_failure_returns_false(monkeypatch, data, capsys):
    monkeypatch.setattr(push.hub, 'push', Mock(side_effect=RuntimeError('SECRET_TOKEN')))
    assert not push.push_prompt_to_langsmith('bug_to_user_story_v2', data)
    assert 'SECRET_TOKEN' not in capsys.readouterr().out

def test_frozen_files_unchanged():
    manifest=json.loads((ROOT/'docs/upstream-integrity.json').read_text())
    for name,digest in manifest.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    assert len((ROOT/'datasets/bug_to_user_story.jsonl').read_text().splitlines())==15
