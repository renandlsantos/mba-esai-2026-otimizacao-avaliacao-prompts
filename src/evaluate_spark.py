"""Complementary local Spark evaluation; never claims LangSmith acceptance."""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict
from langchain_core.messages import HumanMessage

from dotenv import dotenv_values
from openai import OpenAI
import yaml


ROOT = Path(__file__).resolve().parents[1]


class EvaluationError(RuntimeError):
    """Safe error without provider request, credentials or raw response."""


class SparkModel:
    def __init__(self, client, model):
        if model not in {"spark/code", "spark/fast"}:
            raise EvaluationError("Modelo Spark não permitido.")
        self.client, self.model = client, model

    def invoke(self, messages):
        wire = [{"role": "system" if m.type == "system" else "user", "content": m.content}
                for m in messages]
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=wire, temperature=0, max_tokens=4096,
                timeout=300)
            choice = response.choices[0]
            content = choice.message.content
            if choice.finish_reason != "stop" or not isinstance(content, str) or not content.strip():
                raise ValueError("Incomplete completion")
            # Deliberately ignore reasoning_content and all raw provider metadata.
            print(f"{self.model}: resposta concluída", flush=True)
            return SimpleNamespace(content=content)
        except Exception:
            raise EvaluationError("Resposta Spark indisponível ou incompleta.") from None


def frozen_functions(judge):
    # Compile only original function definitions: module imports execute load_dotenv()
    # and search ancestors. No original module or ambient configuration is executed.
    namespace = {"json": json, "math": math, "Dict": Dict, "Any": Any,
                 "HumanMessage": HumanMessage, "get_evaluator_llm": lambda: judge,
                 "print": lambda *args, **kwargs: None}
    wanted = {"evaluate_f1_score", "evaluate_clarity", "evaluate_precision", "parse_judgment"}
    for filename in ("metrics.py", "strict_metrics.py"):
        tree = ast.parse((ROOT / "src" / filename).read_text())
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted and (filename == "metrics.py" or node.name == "parse_judgment")]
        exec(compile(ast.Module(body=functions, type_ignores=[]), filename, "exec"), namespace)
    return namespace


def score_answer(judge, question, answer, reference):
    scores = {}
    namespace = frozen_functions(judge)
    for name, function, fields in (
        ("f1_score", "evaluate_f1_score", ("precision", "recall")),
        ("clarity", "evaluate_clarity", ("score",)),
        ("precision", "evaluate_precision", ("score",)),
    ):
        namespace["extract_json_from_response"] = lambda text, fields=fields: namespace["parse_judgment"](text, fields)
        isolated = namespace[function]
        result = isolated(question, answer, reference)
        value = result.get("score")
        if (str(result.get("reasoning", "")).lower().startswith(("erro na avaliação", "erro ao processar"))
                or isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not 0 <= value <= 1):
            raise EvaluationError("Juiz rejeitado; nenhum score sintético foi registrado.")
        scores[name] = value
    scores["helpfulness"] = (scores["clarity"] + scores["precision"]) / 2
    scores["correctness"] = (scores["f1_score"] + scores["precision"]) / 2
    return scores


def evaluate_version(version, generator, judge, output, limit=15, resume=False):
    from langchain_core.messages import HumanMessage, SystemMessage

    prompt_path = ROOT / f"prompts/bug_to_user_story_{version}.yml"
    dataset_path = ROOT / "datasets/bug_to_user_story.jsonl"
    prompt = yaml.safe_load(prompt_path.read_text())[f"bug_to_user_story_{version}"]
    cases = [json.loads(line) for line in dataset_path.read_text().splitlines() if line.strip()]
    if len(cases) != 15:
        raise EvaluationError("Dataset exige exatamente 15 exemplos.")
    if not 1 <= limit <= 15:
        raise EvaluationError("Limite deve estar entre 1 e 15.")
    if output.exists() and not resume:
        raise EvaluationError("Destino já existe; use --resume com configuração idêntica.")
    report = {"provider": "Spark local", "version": version, "generator": generator.model,
              "judge": judge.model, "concurrency": 1, "temperature": 0, "max_tokens": 4096,
              "timeout_seconds": 300, "langsmith_acceptance": False,
              "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in [prompt_path, dataset_path, ROOT / "src/metrics.py"]},
              "complete": False, "examples": []}
    if resume:
        if not output.exists():
            raise EvaluationError("Checkpoint ausente.")
        saved = json.loads(output.read_text())
        for key in report:
            if key not in {"complete", "examples"} and saved.get(key) != report[key]:
                raise EvaluationError("Checkpoint incompatível com configuração ou insumos atuais.")
        rows = saved.get("examples", [])
        if not isinstance(rows, list) or len(rows) > 15:
            raise EvaluationError("Checkpoint inválido.")
        for index, row in enumerate(rows, 1):
            if row.get("index") != index or not isinstance(row.get("answer"), str) or not row["answer"].strip():
                raise EvaluationError("Checkpoint inválido.")
            scores = row.get("scores", {})
            if set(scores) != {"f1_score", "clarity", "precision", "helpfulness", "correctness"} or any(
                    isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1
                    for v in scores.values()):
                raise EvaluationError("Checkpoint inválido.")
        report["examples"] = rows
    output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(output)

    save()
    for index, case in enumerate(cases, 1):
        if index <= len(report["examples"]):
            continue
        if index > limit or output.with_suffix(".stop").exists():
            break
        bug = case["inputs"]["bug_report"]
        messages = [SystemMessage(content=prompt["system_prompt"].replace("{bug_report}", bug)),
                    HumanMessage(content=prompt["user_prompt"].replace("{bug_report}", bug))]
        answer = generator.invoke(messages).content
        scores = score_answer(judge, bug, answer, case["outputs"]["reference"])
        report["examples"].append({"index": index, "answer": answer, "scores": scores})
        save()
        print(f"{version}: {index}/15 concluídos", flush=True)
    if len(report["examples"]) != 15:
        save()
        return report
    report["means"] = {key: sum(row["scores"][key] for row in report["examples"]) / 15
                       for key in report["examples"][0]["scores"]}
    report["passed_local_threshold"] = all(v >= 0.8 for v in report["means"].values())
    report["complete"] = True
    save()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=["v1", "v2"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--judge", choices=["spark/fast", "spark/code"], default="spark/fast")
    parser.add_argument("--credentials", type=Path, default=Path.home() / ".config/spark/spark-api.env")
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        config = dotenv_values(args.credentials, interpolate=False)
        base = config.get("SPARK_BASE_URL") or config.get("OPENAI_BASE_URL")
        key = config.get("SPARK_API_KEY") or config.get("OPENAI_API_KEY")
        if not base or not key:
            raise EvaluationError("Configuração Spark ausente.")
        client = OpenAI(base_url=base, api_key=key, timeout=300, max_retries=0)
        result = evaluate_version(args.version, SparkModel(client, "spark/code"),
                                  SparkModel(client, args.judge), args.output, args.limit, args.resume)
        print(json.dumps({"means": result.get("means"), "complete": result["complete"], "langsmith_acceptance": False}))
        return 1 if result["complete"] and not result["passed_local_threshold"] else 0
    except Exception:
        print("Avaliação interrompida; evidência parcial preservada, erro redigido.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
