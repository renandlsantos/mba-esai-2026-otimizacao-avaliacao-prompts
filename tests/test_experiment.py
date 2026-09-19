from types import SimpleNamespace
import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import evaluate_experiment as experiment


def row(score=0.9):
    return {'run':SimpleNamespace(id='test-id',error=None,outputs={'answer':'story'}),
            'evaluation_results':{'results':[SimpleNamespace(key=key,score=score) for key in experiment.METRICS]}}


def test_summary_requires_all_fifteen_examples():
    with pytest.raises(ValueError):
        experiment.summarize([row()]*14)


def test_summary_does_not_hide_failed_generation():
    broken=row();broken['run'].error='failed'
    with pytest.raises(ValueError):
        experiment.summarize([row()]*14+[broken])


def test_every_metric_must_pass():
    rows=[row() for _ in range(15)]
    for r in rows:
        r['evaluation_results']['results'][0].score=0.79
    report=experiment.summarize(rows)
    assert report['average']>0.8
    assert report['passed'] is False


@pytest.mark.parametrize('score',[None,float('nan'),float('inf'),1.1,-0.1,True])
def test_summary_rejects_invalid_scores(score):
    with pytest.raises(ValueError):
        experiment.summarize([row(score)]*15)


def test_grade_uses_original_metric_formulas(monkeypatch):
    monkeypatch.setattr(experiment,'evaluate_f1_score',lambda *a:{'score':0.8})
    monkeypatch.setattr(experiment,'evaluate_clarity',lambda *a:{'score':0.9})
    monkeypatch.setattr(experiment,'evaluate_precision',lambda *a:{'score':1.0})
    run=SimpleNamespace(error=None,outputs={'answer':'story'})
    example=SimpleNamespace(inputs={'bug_report':'bug'},outputs={'reference':'ref'})
    feedback={x['key']:x['score'] for x in experiment.grade(run,example)['results']}
    assert feedback['helpfulness']==pytest.approx(0.95)
    assert feedback['correctness']==pytest.approx(0.9)


def test_experiment_contract_creates_dataset_and_metadata(monkeypatch):
    from unittest.mock import Mock
    prompt=Mock();prompt.metadata={'lc_hub_commit_hash':'abc'}
    prompt.__or__=Mock(return_value=Mock())
    monkeypatch.setattr(experiment.hub,'pull',Mock(return_value=prompt))
    monkeypatch.setattr(experiment,'get_llm',Mock(return_value=object()))
    class Results(list):
        experiment_name='test-experiment'
    evaluator=Mock(return_value=Results([row() for _ in range(15)]))
    monkeypatch.setattr(experiment,'evaluate',evaluator)
    client=Mock()
    client.create_dataset.return_value=SimpleNamespace(id='dataset-id')
    client.read_project.return_value=SimpleNamespace(url='https://example.test/dashboard')
    result=experiment.run_experiment('owner/prompt:abc','v2',client,'test-dataset')
    assert result['passed'] is True
    assert result['hub_commit']=='abc'
    assert len(client.create_examples.call_args.kwargs['inputs'])==15
    assert evaluator.call_args.kwargs['max_concurrency']==1
    assert evaluator.call_args.kwargs['evaluators']==[experiment.grade]
