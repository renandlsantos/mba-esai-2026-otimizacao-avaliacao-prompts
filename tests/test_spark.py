import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import evaluate_spark as spark


class Fake:
    model = "test-only"
    def invoke(self, messages):
        return SimpleNamespace(content=json.dumps({"precision": 0.5, "recall": 1,
                                                   "score": 0.8, "reasoning": "Teste"}))


def test_frozen_formula_private_globals():
    original = spark.frozen_functions(Fake())
    scores = spark.score_answer(Fake(), "q", "a", "r")
    assert scores["f1_score"] == 0.6667
    assert scores["correctness"] == pytest.approx((0.6667 + 0.8) / 2)
    assert original["get_evaluator_llm"] is not spark.frozen_functions(Fake())["get_evaluator_llm"]


def test_bad_judge_redacted(capsys):
    class Bad(Fake):
        def invoke(self, messages):
            raise RuntimeError("SECRET request body")
    with pytest.raises(spark.EvaluationError):
        spark.score_answer(Bad(), "q", "a", "r")
    assert "SECRET" not in capsys.readouterr().out


@pytest.mark.parametrize("finish,content", [("length", "partial"), ("stop", ""), ("stop", None)])
def test_reject_incomplete_provider(finish, content):
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:
        SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish, message=SimpleNamespace(content=content))]))))
    with pytest.raises(spark.EvaluationError):
        spark.SparkModel(client, "spark/fast").invoke([])


def test_all_fifteen_and_no_overwrite(tmp_path):
    path = tmp_path / "result.json"
    result = spark.evaluate_version("v1", Fake(), Fake(), path)
    assert result["complete"] and len(result["examples"]) == 15
    assert result["langsmith_acceptance"] is False
    assert not result["passed_local_threshold"]
    with pytest.raises(spark.EvaluationError):
        spark.evaluate_version("v1", Fake(), Fake(), path)


def test_failure_preserves_incomplete_evidence(tmp_path):
    class Bad(Fake):
        def invoke(self, messages):
            return SimpleNamespace(content="{}")
    path = tmp_path / "result.json"
    with pytest.raises(spark.EvaluationError):
        spark.evaluate_version("v2", Fake(), Bad(), path)
    result = json.loads(path.read_text())
    assert not result["complete"] and not result["examples"]
    assert "means" not in result


def test_import_does_not_discover_ancestor_env():
    import subprocess
    program = "import sys; sys.path.insert(0, 'src'); import evaluate_spark; assert 'metrics' not in sys.modules; assert 'utils' not in sys.modules; evaluate_spark.frozen_functions(None)"
    result = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True)
    assert result.returncode == 0
    assert "dotenv" not in result.stderr


def test_limit_and_resume_identical_checkpoint(tmp_path):
    path = tmp_path / "partial.json"
    partial = spark.evaluate_version("v1", Fake(), Fake(), path, limit=3)
    assert not partial["complete"] and len(partial["examples"]) == 3
    assert "means" not in partial and "passed_local_threshold" not in partial
    completed = spark.evaluate_version("v1", Fake(), Fake(), path, resume=True)
    assert completed["complete"] and len(completed["examples"]) == 15
    assert completed["examples"][:3] == partial["examples"]
    with pytest.raises(spark.EvaluationError):
        spark.evaluate_version("v2", Fake(), Fake(), path, resume=True)


def test_stop_file_preserves_checkpoint(tmp_path):
    path = tmp_path / "partial.json"
    path.with_suffix(".stop").touch()
    result = spark.evaluate_version("v1", Fake(), Fake(), path)
    assert not result["complete"] and len(result["examples"]) == 0


def test_provider_configuration_and_reasoning_excluded():
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(
            content="Final", reasoning_content="INTERNAL_REASONING"))])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    result = spark.SparkModel(client, "spark/fast").invoke([])
    assert result.__dict__ == {"content": "Final"}
    assert calls[0]["timeout"] == 300 and calls[0]["max_tokens"] == 4096
    assert calls[0]["temperature"] == 0


def test_provider_exception_redacted():
    def create(**kwargs):
        raise RuntimeError("SECRET AUTHORIZATION REQUEST")
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with pytest.raises(spark.EvaluationError) as caught:
        spark.SparkModel(client, "spark/code").invoke([])
    assert "SECRET" not in str(caught.value)
    assert caught.value.__suppress_context__


@pytest.mark.parametrize("complete,passed,expected", [(True, False, 1), (True, True, 0), (False, False, 0)])
def test_main_exit_code_and_no_credential_interpolation(monkeypatch, tmp_path, complete, passed, expected):
    monkeypatch.setattr(sys, "argv", ["evaluate_spark", "--version", "v1", "--output", str(tmp_path / "out.json")])
    def config(path, *, interpolate):
        assert interpolate is False
        return {"SPARK_BASE_URL": "http://test.invalid/v1", "SPARK_API_KEY": "test-only"}
    monkeypatch.setattr(spark, "dotenv_values", config)
    monkeypatch.setattr(spark, "OpenAI", lambda **kwargs: object())
    monkeypatch.setattr(spark, "evaluate_version", lambda *args: {"complete": complete, "passed_local_threshold": passed})
    assert spark.main() == expected
