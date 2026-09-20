from contextlib import contextmanager
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import evaluate_langsmith_spark as runner


class FakeModel:
    model = "test-only"
    def invoke(self, messages):
        return SimpleNamespace(content=json.dumps({"precision": .9, "recall": .9, "score": .9, "reasoning": "Teste"}))


class FakeClient:
    def __init__(self):
        self.examples, self.feedback = [], {}
    def create_dataset(self, **kwargs):
        return SimpleNamespace(id="dataset")
    def create_example(self, **kwargs):
        result = SimpleNamespace(id=str(uuid4()), **kwargs)
        self.examples.append(result)
        return result
    def list_examples(self, **kwargs):
        return self.examples
    def create_project(self, *args, **kwargs):
        assert kwargs["reference_dataset_id"] == "dataset"
        return SimpleNamespace(id="project")
    def read_project(self, **kwargs):
        return SimpleNamespace(id="project", url="https://test.invalid/dashboard")
    def create_feedback(self, run_id, key, **kwargs):
        self.feedback.setdefault(str(run_id), []).append(SimpleNamespace(key=key, score=kwargs["score"]))
    def list_feedback(self, run_ids):
        return self.feedback[run_ids[0]]
    def read_run(self, run_id, **kwargs):
        return SimpleNamespace(error=None, outputs={"answer": "test"}, child_runs=[
            SimpleNamespace(error=None, run_type="llm", outputs={"content": "test"}) for _ in range(4)])
    def get_run_url(self, **kwargs):
        return "https://test.invalid/trace"


@pytest.fixture
def tracing(monkeypatch):
    calls = []
    @contextmanager
    def trace(name, **kwargs):
        calls.append((name, kwargs))
        yield SimpleNamespace(id=uuid4(), end=lambda **kw: None)
    @contextmanager
    def context(**kwargs):
        assert kwargs["enabled"] is True
        yield
    monkeypatch.setattr(runner, "trace", trace)
    monkeypatch.setattr(runner, "tracing_context", context)
    return calls


def test_partial_then_resume_full_without_repeating_cases(tmp_path, tracing):
    client = FakeClient()
    args = dict(version="v2", output=tmp_path / "report.json", base_project="test")
    partial = runner.run_experiment(client, FakeModel(), FakeModel(), limit=1, **args)
    assert not partial["complete"] and "means" not in partial
    assert partial["remote_feedback_verified"] == 5
    result = runner.run_experiment(client, FakeModel(), FakeModel(), resume=True, **args)
    assert result["complete"] and result["passed_metric_threshold"]
    assert result["academic_acceptance"] is False
    assert result["remote_feedback_verified"] == 75
    assert len(tracing) == 75  # 15 roots + generation and three actual delegate calls per case.
    assert len(client.examples) == 15


def test_resume_rejects_remote_dataset_mutation(tmp_path, tracing):
    client = FakeClient()
    args = dict(version="v2", output=tmp_path / "report.json", base_project="test")
    runner.run_experiment(client, FakeModel(), FakeModel(), limit=1, **args)
    client.examples[0].inputs = {"bug_report": "changed"}
    with pytest.raises(runner.EvaluationError, match="diverge"):
        runner.run_experiment(client, FakeModel(), FakeModel(), resume=True, **args)


def test_missing_remote_feedback_never_completes(tmp_path, tracing):
    client = FakeClient()
    client.list_feedback = lambda **kwargs: []
    with pytest.raises(runner.EvaluationError, match="Feedback"):
        runner.run_experiment(client, FakeModel(), FakeModel(), version="v2",
                              output=tmp_path / "report.json", base_project="test", limit=1)
    report = json.loads((tmp_path / "report.json").read_text())
    assert not report["complete"] and "means" not in report


def test_hub_mismatch_rejected_before_inference():
    client = SimpleNamespace(pull_prompt_commit=lambda ref: SimpleNamespace(commit_hash="hash"),
                             pull_prompt=lambda ref: SimpleNamespace(invoke=lambda values: SimpleNamespace(messages=[])))
    with pytest.raises(runner.EvaluationError, match="difere"):
        runner.verify_hub(client, "owner/name", {"system_prompt": "s", "user_prompt": "{bug_report}"},
                          [{"inputs": {"bug_report": "bug"}}])


def test_import_never_imports_frozen_module():
    import subprocess
    result = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0,'src'); import evaluate_langsmith_spark; assert 'utils' not in sys.modules; assert 'metrics' not in sys.modules"], capture_output=True, text=True)
    assert result.returncode == 0 and "dotenv" not in result.stderr


@pytest.mark.parametrize("mutation", ["boolean", "nan", "missing", "duplicate", "too_many", "runner_hash", "judge", "judge_format"])
def test_resume_rejects_invalid_checkpoint(tmp_path, tracing, mutation):
    client = FakeClient()
    path = tmp_path / "report.json"
    args = dict(version="v2", output=path, base_project="test")
    runner.run_experiment(client, FakeModel(), FakeModel(), limit=1, **args)
    data = json.loads(path.read_text())
    if mutation == "boolean": data["examples"][0]["scores"]["clarity"] = True
    elif mutation == "nan": data["examples"][0]["scores"]["clarity"] = float("nan")
    elif mutation == "missing": del data["examples"][0]["scores"]["clarity"]
    elif mutation == "duplicate": data["examples"].append(data["examples"][0].copy())
    elif mutation == "too_many": data["examples"] *= 16
    elif mutation == "runner_hash": data["metadata"]["runner_sha256"] = "different"
    elif mutation == "judge": data["metadata"]["judge"] = "spark/fast"
    elif mutation == "judge_format": data["metadata"]["judge_response_format"] = "json_object"
    path.write_text(json.dumps(data))
    with pytest.raises(runner.EvaluationError):
        runner.run_experiment(client, FakeModel(), FakeModel(), resume=True, **args)


def test_legacy_adoption_requires_explicit_option_and_archives_exact_bytes(tmp_path, tracing):
    client = FakeClient()
    path = tmp_path / "report.json"
    args = dict(version="v2", output=path, base_project="test")
    runner.run_experiment(client, FakeModel(), FakeModel(), limit=1, **args)
    data = json.loads(path.read_text()); del data["metadata"]["runner_sha256"]
    original = json.dumps(data).encode(); path.write_bytes(original)
    with pytest.raises(runner.EvaluationError):
        runner.run_experiment(client, FakeModel(), FakeModel(), resume=True, **args)
    result = runner.run_experiment(client, FakeModel(), FakeModel(), resume=True, adopt_legacy=True, limit=1, **args)
    assert path.with_suffix(".legacy-smoke.json").read_bytes() == original
    assert result["checkpoint_migration"]["original_runner_sha256"] is None


def test_versions_share_exact_same_dataset(tmp_path, tracing):
    client = FakeClient()
    runner.run_experiment(client, FakeModel(), FakeModel(), version="v1", output=tmp_path / "v1.json", base_project="test", limit=1)
    result = runner.run_experiment(client, FakeModel(), FakeModel(), version="v2", output=tmp_path / "v2.json", base_project="test", dataset_id="dataset", limit=1)
    assert result["dataset_id"] == "dataset" and len(client.examples) == 15


def test_feedback_transport_rounding_keeps_academic_raw_value():
    raw = {"correctness": (0.9744 + 1) / 2, "helpfulness": (0.6667 + .8) / 2}
    wire = runner.feedback_scores(raw)
    assert wire["correctness"] == .9872
    assert raw["correctness"] == .9872000000000001
    assert wire["helpfulness"] == round(raw["helpfulness"], 4)


def test_runner_upgrade_requires_proven_previous_source(tmp_path, tracing):
    import hashlib
    client = FakeClient(); path = tmp_path / "report.json"
    args = dict(version="v2", output=path, base_project="test")
    runner.run_experiment(client, FakeModel(), FakeModel(), limit=1, **args)
    data = json.loads(path.read_text()); previous = b"previous reviewed source"
    old_hash = hashlib.sha256(previous).hexdigest(); data["metadata"]["runner_sha256"] = old_hash
    path.write_text(json.dumps(data))
    with pytest.raises(runner.EvaluationError, match="comprovada"):
        runner.run_experiment(client, FakeModel(), FakeModel(), resume=True, adopt_upgrade=True, **args)
    (tmp_path / ("runner-" + old_hash + ".py")).write_bytes(previous)
    result = runner.run_experiment(client, FakeModel(), FakeModel(), resume=True, adopt_upgrade=True, limit=1, **args)
    assert result["runner_upgrades"][0]["previous_runner_sha256"] == old_hash
    assert path.with_name(path.stem + ".before-" + old_hash[:12] + ".json").exists()


def test_cli_defaults_to_same_author_selected_spark_model(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "argv", ["evaluate_langsmith_spark", "--version", "v1", "--output", str(tmp_path / "report.json")])
    monkeypatch.setattr(runner, "dotenv_values", lambda *args, **kwargs: {
        "LANGSMITH_ENDPOINT": "https://test.invalid", "LANGSMITH_API_KEY": "test-only",
        "LANGSMITH_PROJECT": "test", "SPARK_BASE_URL": "https://test.invalid/v1", "SPARK_API_KEY": "test-only"})
    monkeypatch.setattr(runner, "Client", lambda **kwargs: object())
    monkeypatch.setattr(runner, "OpenAI", lambda **kwargs: object())
    def execute(client, generator, judge, **kwargs):
        assert generator.model == judge.model == "spark/code"
        return {"complete": False, "dashboard_url": "https://test.invalid/report"}
    monkeypatch.setattr(runner, "run_experiment", execute)
    assert runner.main() == 0


class JsonFakeModel(FakeModel):
    json_mode = True


def test_judge_contract_recorded_in_metadata_feedback_and_spans(tmp_path, tracing):
    client = FakeClient()
    report = runner.run_experiment(client, FakeModel(), JsonFakeModel(), version="v2",
                                   output=tmp_path / "report.json", base_project="test", limit=1)
    assert report["metadata"]["judge_response_format"] == "json_object"
    formats = {name: kwargs["metadata"].get("response_format")
               for name, kwargs in tracing if name.startswith(("generation:", "judge:"))}
    assert formats == {"generation:test-only": "text", "judge:test-only": "json_object"}
    assert all(item.score is not None for item in client.feedback[report["examples"][0]["run_id"]])
