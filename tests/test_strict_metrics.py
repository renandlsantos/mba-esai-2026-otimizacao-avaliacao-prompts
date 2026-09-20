import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import metrics
import strict_metrics
import evaluate_experiment as experiment


@pytest.mark.parametrize("payload", [
    {}, {"reasoning": "Explicação sem notas"},
    {"precision": 0.9, "reasoning": "Recall ausente"},
    {"score": 0.9, "reasoning": "F1 exige precision e recall"},
    {"precision": True, "recall": 0.9, "reasoning": "Boolean não é nota"},
    {"precision": "0.9", "recall": 0.9, "reasoning": "String não é nota"},
    {"precision": float("nan"), "recall": 0.9, "reasoning": "Não finito"},
    {"precision": 1.1, "recall": 0.9, "reasoning": "Fora do intervalo"},
    {"precision": 0.9, "recall": 0.9, "reasoning": " "},
    [],
])
def test_incomplete_judge_cannot_enter_experiment(monkeypatch, payload):
    model = SimpleNamespace(invoke=lambda messages: SimpleNamespace(content=json.dumps(payload)))
    monkeypatch.setattr(metrics, "get_evaluator_llm", lambda: model)
    run = SimpleNamespace(error=None, outputs={"answer": "story"})
    example = SimpleNamespace(inputs={"bug_report": "bug"}, outputs={"reference": "ref"})
    # Reject before summarize: 14 good rows cannot dilute this failure into a pass.
    with pytest.raises(ValueError, match="Avaliador informou erro"):
        experiment.grade(run, example)


@pytest.mark.parametrize("function", [strict_metrics.evaluate_clarity, strict_metrics.evaluate_precision])
@pytest.mark.parametrize("payload", [{}, {"reasoning": "Sem nota"}, {"score": True, "reasoning": "Inválido"}, {"score": 0.8}])
def test_scalar_metric_requires_complete_schema(monkeypatch, function, payload):
    monkeypatch.setattr(metrics, "get_evaluator_llm", lambda: SimpleNamespace(
        invoke=lambda messages: SimpleNamespace(content=json.dumps(payload))))
    result = function("bug", "answer", "reference")
    assert result["reasoning"].startswith("Erro na avaliação")


def test_valid_zero_and_original_f1_formula_are_preserved(monkeypatch):
    responses = iter([
        {"precision": 0.5, "recall": 1.0, "reasoning": "Metade precisa, cobertura total"},
        {"score": 0.0, "reasoning": "Sem clareza"},
        {"score": 0.8, "reasoning": "Precisão parcial"},
    ])
    messages_seen = []
    def invoke(messages):
        messages_seen.append(messages)
        return SimpleNamespace(content=json.dumps(next(responses)))
    monkeypatch.setattr(metrics, "get_evaluator_llm", lambda: SimpleNamespace(invoke=invoke))
    original_parser = metrics.extract_json_from_response
    run = SimpleNamespace(error=None, outputs={"answer": "story"})
    example = SimpleNamespace(inputs={"bug_report": "bug"}, outputs={"reference": "ref"})
    scores = {item["key"]: item["score"] for item in experiment.grade(run, example)["results"]}
    assert scores["f1_score"] == 0.6667
    assert scores["clarity"] == 0
    assert scores["helpfulness"] == 0.4
    assert scores["correctness"] == pytest.approx((0.6667 + 0.8) / 2)
    assert metrics.extract_json_from_response is original_parser
    assert "calcular PRECISION e RECALL" in messages_seen[0][0].content
