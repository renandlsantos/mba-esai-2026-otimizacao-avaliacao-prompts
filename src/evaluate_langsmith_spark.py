"""Real Spark calls with explicit LangSmith tracing and dataset-backed experiments."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
from pathlib import Path

from dotenv import dotenv_values
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import Client, trace, tracing_context
from openai import OpenAI
import yaml

from evaluate_spark import EvaluationError, ROOT, SparkModel, score_answer

METRICS = ("f1_score", "clarity", "precision", "helpfulness", "correctness")
V1_REF = "leonanluppi/bug_to_user_story_v1:2950c33dbd7ffaed2e440b50adfd7769d183f90faf0bae5aa4864354f88e4073"


def messages_for(prompt, bug):
    return [SystemMessage(content=prompt["system_prompt"].replace("{bug_report}", bug)),
            HumanMessage(content=prompt["user_prompt"].replace("{bug_report}", bug))]


class TracedSparkModel:
    def __init__(self, model, client, purpose):
        self.delegate, self.client, self.purpose = model, client, purpose
        self.model = model.model

    def invoke(self, messages):
        inputs = {"messages": [{"role": "system" if m.type == "system" else "user",
                                "content": m.content} for m in messages]}
        with trace(f"{self.purpose}:{self.model}", run_type="llm", inputs=inputs,
                   client=self.client, metadata={"ls_provider": "openai",
                   "ls_model_name": self.model, "ls_temperature": 0,
                   "provider_deployment": "Spark", "max_tokens": 4096}) as span:
            answer = self.delegate.invoke(messages)
            span.end(outputs={"choices": [{"message": {"role": "assistant", "content": answer.content}}]})
            return answer


def write_report(output, report):
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(output)


def verify_hub(client, ref, prompt, cases):
    if not ref:
        return {"prompt_source": "local-yaml", "hub_ref": None, "hub_commit": None}
    commit = client.pull_prompt_commit(ref)
    pinned = ref.split(":")[0] + ":" + commit.commit_hash
    remote = client.pull_prompt(pinned)
    for case in cases:
        bug = case["inputs"]["bug_report"]
        if [(m.type, m.content) for m in remote.invoke({"bug_report": bug}).messages] != [
                (m.type, m.content) for m in messages_for(prompt, bug)]:
            raise EvaluationError("Snapshot Hub difere do YAML; avaliação cancelada.")
    return {"prompt_source": "hub-verified-local-equivalent", "hub_ref": pinned,
            "hub_commit": commit.commit_hash}


def feedback_scores(scores):
    """LangSmith accepts four decimal places; retain raw academic values separately."""
    return {key: round(value, 4) for key, value in scores.items()}


def verify_remote(client, report):
    rows = report["examples"]
    for row in rows:
        feedback = list(client.list_feedback(run_ids=[row["run_id"]]))
        actual = {item.key: item.score for item in feedback}
        if actual != feedback_scores(row["scores"]):
            raise EvaluationError("Feedback remoto ausente ou divergente.")
    traces = []
    for row in rows[:3]:
        run = client.read_run(row["run_id"], load_child_runs=True)
        children = run.child_runs or []
        if run.error or not run.outputs or len(children) != 4 or any(
                child.error or child.run_type != "llm" or not child.outputs for child in children):
            raise EvaluationError("Trace remoto não comprova geração e três julgamentos.")
        traces.append(client.get_run_url(run=run, project_id=report["project_id"]))
    return traces


def run_experiment(client, generator, judge, *, version, output, base_project,
                   prompt_ref=None, limit=15, resume=False, dataset_id=None, adopt_legacy=False, adopt_upgrade=False):
    if not 1 <= limit <= 15:
        raise EvaluationError("Limite deve estar entre 1 e 15.")
    source = ROOT / "datasets/bug_to_user_story.jsonl"
    prompt_path = ROOT / f"prompts/bug_to_user_story_{version}.yml"
    cases = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    if len(cases) != 15:
        raise EvaluationError("Dataset exige 15 exemplos.")
    prompt = yaml.safe_load(prompt_path.read_text())[f"bug_to_user_story_{version}"]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [source, prompt_path, ROOT / "src/metrics.py", ROOT / "src/strict_metrics.py",
                        ROOT / "src/evaluate_spark.py"]}
    metadata = {"runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "version": version, "hashes": hashes, "generator": generator.model,
                "judge": judge.model, "temperature": 0, "max_tokens": 4096,
                "timeout_seconds": 300, "concurrency": 1, "base_project": base_project,
                **verify_hub(client, prompt_ref, prompt, cases)}
    if resume:
        report = json.loads(output.read_text())
        old_metadata = report["metadata"]
        legacy = "runner_sha256" not in old_metadata
        upgraded = not legacy and old_metadata.get("runner_sha256") != metadata["runner_sha256"]
        comparable = {k: v for k, v in metadata.items() if k != "runner_sha256"}
        old_comparable = {k: v for k, v in old_metadata.items() if k != "runner_sha256"}
        if old_comparable != comparable or (legacy and not adopt_legacy) or (upgraded and not adopt_upgrade):
            raise EvaluationError("Checkpoint incompatível com snapshot/configuração.")
        if upgraded:
            previous_source = output.parent / ("runner-" + old_metadata["runner_sha256"] + ".py")
            if not previous_source.exists() or hashlib.sha256(previous_source.read_bytes()).hexdigest() != old_metadata["runner_sha256"]:
                raise EvaluationError("Fonte anterior não comprovada; migração recusada.")
        if not isinstance(report.get("examples"), list) or len(report["examples"]) > 15:
            raise EvaluationError("Checkpoint inválido.")
        run_ids = set()
        for row in report["examples"]:
            scores = row.get("scores", {})
            if (not isinstance(scores, dict) or set(scores) != set(METRICS)
                    or any(isinstance(v, bool) or not isinstance(v, (int, float))
                           or not math.isfinite(v) or not 0 <= v <= 1 for v in scores.values())
                    or not isinstance(row.get("answer"), str) or not row["answer"].strip()
                    or not isinstance(row.get("run_id"), str) or not row["run_id"]
                    or row["run_id"] in run_ids):
                raise EvaluationError("Checkpoint inválido.")
            run_ids.add(row["run_id"])
        remote_cases = {str(item.id): item for item in client.list_examples(dataset_id=report["dataset_id"])}
        for local, example_id in zip(cases, report["example_ids"], strict=True):
            remote = remote_cases.get(example_id)
            if remote is None or remote.inputs != local["inputs"] or remote.outputs != local["outputs"]:
                raise EvaluationError("Dataset remoto diverge do dataset congelado.")
        if len(remote_cases) != 15:
            raise EvaluationError("Dataset remoto incompleto.")
        for index, row in enumerate(report["examples"], 1):
            if type(row.get("index")) is not int or row["index"] != index or row["example_id"] != report["example_ids"][index - 1]:
                raise EvaluationError("Checkpoint inválido.")
        verify_remote(client, report)
        if upgraded:
            archive = output.with_name(output.stem + ".before-" + old_metadata["runner_sha256"][:12] + ".json")
            if archive.exists():
                raise EvaluationError("Snapshot anterior já existe; não sobrescrever.")
            original = output.read_bytes()
            archive.write_bytes(original)
            report.setdefault("runner_upgrades", []).append({
                "previous_runner_sha256": old_metadata["runner_sha256"],
                "new_runner_sha256": metadata["runner_sha256"],
                "original_report_sha256": hashlib.sha256(original).hexdigest(),
                "reason": "Atualização explícita, fonte anterior comprovada e evidência remota verificada; sem repetir inferência.",
            })
            report["metadata"] = metadata
            write_report(output, report)
        if legacy:
            archive = output.with_suffix(".legacy-smoke.json")
            if archive.exists():
                raise EvaluationError("Arquivo de migração já existe; não sobrescrever.")
            original = output.read_bytes()
            archive.write_bytes(original)
            report["checkpoint_migration"] = {
                "original_report_sha256": hashlib.sha256(original).hexdigest(),
                "original_runner_sha256": None,
                "reason": "Smoke anterior à instrumentação de hash; fonte anterior não comprovada. Insumos e evidência remota verificados; nenhum resultado regenerado.",
            }
            report["metadata"] = metadata
            write_report(output, report)
    else:
        if output.exists():
            raise EvaluationError("Destino existente; use --resume.")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        name = f"{base_project}-Spark-{version}-{stamp}"
        if dataset_id:
            candidates = list(client.list_examples(dataset_id=dataset_id))
            examples = []
            for case in cases:
                matches = [e for e in candidates if e.inputs == case["inputs"] and e.outputs == case["outputs"]]
                if len(matches) != 1:
                    raise EvaluationError("Dataset compartilhado diverge dos casos congelados.")
                examples.append(matches[0])
            if len(candidates) != 15:
                raise EvaluationError("Dataset compartilhado deve ter exatamente 15 casos.")
        else:
            dataset = client.create_dataset(dataset_name=name + "-dataset", description="15 casos originais congelados da fase 294.")
            dataset_id = str(dataset.id)
            examples = [client.create_example(inputs=case["inputs"], outputs=case["outputs"],
                        metadata=case.get("metadata"), dataset_id=dataset_id) for case in cases]
        project = client.create_project(name, reference_dataset_id=dataset_id, metadata=metadata)
        project = client.read_project(project_id=project.id)
        report = {"metadata": metadata, "experiment_name": name, "project_id": str(project.id),
                  "dataset_id": str(dataset_id), "example_ids": [str(e.id) for e in examples],
                  "dashboard_url": project.url, "examples": [], "complete": False,
                  "academic_acceptance": False}
        write_report(output, report)
    traced_generator = TracedSparkModel(generator, client, "generation")
    traced_judge = TracedSparkModel(judge, client, "judge")
    with tracing_context(enabled=True, client=client, project_name=report["experiment_name"]):
        for index, case in enumerate(cases, 1):
            if index <= len(report["examples"]):
                continue
            if index > limit or output.with_suffix(".stop").exists():
                break
            with trace(f"bug-to-user-story-{version}", inputs=case["inputs"], client=client,
                       reference_example_id=report["example_ids"][index - 1], metadata=metadata) as span:
                answer = traced_generator.invoke(messages_for(prompt, case["inputs"]["bug_report"])).content
                scores = score_answer(traced_judge, case["inputs"]["bug_report"], answer, case["outputs"]["reference"])
                span.end(outputs={"answer": answer})
            for key, value in scores.items():
                client.create_feedback(span.id, key, score=round(value, 4), feedback_source_type="model",
                                       source_info={"judge": judge.model, "frozen_metric": True, "raw_metric_score": value})
            report["examples"].append({"index": index, "example_id": report["example_ids"][index - 1],
                                       "run_id": str(span.id), "answer": answer, "scores": scores})
            write_report(output, report)
            print(f"LangSmith {version}: {index}/15 persistidos", flush=True)
    report["trace_urls"] = verify_remote(client, report)
    report["remote_feedback_verified"] = 5 * len(report["examples"])
    if len(report["examples"]) == 15:
        report["means"] = {key: sum(row["scores"][key] for row in report["examples"]) / 15 for key in METRICS}
        report["passed_metric_threshold"] = all(value >= .8 for value in report["means"].values())
        report["complete"] = True
    write_report(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=["v1", "v2"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--adopt-legacy-checkpoint", action="store_true", help="Arquiva e adota smoke sem hash após verificar insumos e traces remotos")
    parser.add_argument("--adopt-runner-upgrade", action="store_true", help="Exige snapshot comprovado do runner anterior e verifica evidência remota")
    parser.add_argument("--prompt-ref")
    parser.add_argument("--dataset-id", help="Mesmo dataset da outra versão para comparação no LangSmith")
    args = parser.parse_args()
    # Provider exceptions are redacted before tracing; suppress SDK transport logs.
    logging.getLogger("langsmith").addHandler(logging.NullHandler())
    logging.getLogger("langsmith").propagate = False
    try:
        ls = dotenv_values(Path.home() / ".config/langsmith/mba-esai.env", interpolate=False)
        spark = dotenv_values(Path.home() / ".config/spark/spark-api.env", interpolate=False)
        client = Client(api_url=ls["LANGSMITH_ENDPOINT"], api_key=ls["LANGSMITH_API_KEY"], auto_batch_tracing=False)
        provider = OpenAI(base_url=spark.get("SPARK_BASE_URL") or spark["OPENAI_BASE_URL"],
                          api_key=spark.get("SPARK_API_KEY") or spark["OPENAI_API_KEY"], timeout=300, max_retries=0)
        report = run_experiment(client, SparkModel(provider, "spark/code"), SparkModel(provider, "spark/fast"),
                                version=args.version, output=args.output, base_project=ls["LANGSMITH_PROJECT"],
                                prompt_ref=args.prompt_ref or (V1_REF if args.version == "v1" else None),
                                limit=args.limit, resume=args.resume, dataset_id=args.dataset_id, adopt_legacy=args.adopt_legacy_checkpoint, adopt_upgrade=args.adopt_runner_upgrade)
        print(json.dumps({"complete": report["complete"], "means": report.get("means"),
                          "dashboard_url": report["dashboard_url"], "academic_acceptance": False}))
        return int(report["complete"] and not report["passed_metric_threshold"])
    except Exception as error:
        print(f"Experimento interrompido ({type(error).__name__}); detalhes sensíveis omitidos, checkpoint preservado.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
