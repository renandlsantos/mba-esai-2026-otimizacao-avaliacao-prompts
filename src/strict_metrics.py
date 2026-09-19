"""Validate raw judge schemas while preserving frozen prompts and formulas.

The starter has no parser-injection parameter. FunctionType reuses each frozen
function's bytecode with a private globals dictionary containing the strict
parser. It neither modifies metrics.py nor patches shared module state, so
parallel evaluator calls cannot exchange parser requirements.
"""
import json
import math
from types import FunctionType

import metrics


def parse_judgment(text, score_fields):
    if not isinstance(text, str):
        raise ValueError("Juiz deve devolver JSON textual.")
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # Same tolerance for surrounding prose as the original parser, no defaults.
        start, end = text.find("{"), text.rfind("}") + 1
        if start < 0 or end <= start:
            raise ValueError("Juiz não devolveu objeto JSON.") from None
        try:
            result = json.loads(text[start:end])
        except json.JSONDecodeError:
            raise ValueError("JSON do juiz inválido.") from None
    if not isinstance(result, dict):
        raise ValueError("Juiz deve devolver objeto JSON.")
    if not isinstance(result.get("reasoning"), str) or not result["reasoning"].strip():
        raise ValueError("Juiz não forneceu reasoning válido.")
    for field in score_fields:
        value = result.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"Juiz não forneceu {field} numérico entre 0 e 1.")
    return result


def evaluate_strict(original, score_fields, question, answer, reference):
    def parser(text):
        return parse_judgment(text, score_fields)

    isolated_globals = dict(original.__globals__)
    isolated_globals["extract_json_from_response"] = parser
    checked = FunctionType(original.__code__, isolated_globals, original.__name__,
                           original.__defaults__, original.__closure__)
    return checked(question, answer, reference)


def evaluate_f1_score(question, answer, reference):
    return evaluate_strict(metrics.evaluate_f1_score, ("precision", "recall"), question, answer, reference)


def evaluate_clarity(question, answer, reference):
    return evaluate_strict(metrics.evaluate_clarity, ("score",), question, answer, reference)


def evaluate_precision(question, answer, reference):
    return evaluate_strict(metrics.evaluate_precision, ("score",), question, answer, reference)
