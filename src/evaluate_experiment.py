"""Experimentos rastreáveis v1/v2 usando as métricas acadêmicas intactas.

Não executa avaliações ao importar. A CLI faz chamadas pagas ao provedor configurado.
"""
import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from langchain import hub
from langsmith import Client
from langsmith.evaluation import evaluate
from strict_metrics import evaluate_f1_score, evaluate_clarity, evaluate_precision
from utils import check_env_vars, get_llm

ROOT = Path(__file__).resolve().parents[1]
METRICS = ('f1_score', 'clarity', 'precision', 'helpfulness', 'correctness')


def grade(run, example):
    """Mesmas três avaliações base e duas médias derivadas do upstream."""
    answer = (run.outputs or {}).get('answer')
    if run.error or not isinstance(answer, str) or not answer.strip():
        raise ValueError('Execução sem resposta válida; não aceitar avaliação incompleta.')
    question = example.inputs['bug_report']
    reference = example.outputs['reference']
    base = {
        'f1_score': evaluate_f1_score(question, answer, reference),
        'clarity': evaluate_clarity(question, answer, reference),
        'precision': evaluate_precision(question, answer, reference),
    }
    scores = {}
    for name, result in base.items():
        value = result.get('score')
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f'Métrica inválida: {name}')
        if result.get('reasoning', '').lower().startswith(('erro na avaliação', 'erro ao processar')):
            raise ValueError(f'Avaliador informou erro: {name}')
        scores[name] = float(value)
    scores['helpfulness'] = (scores['clarity'] + scores['precision']) / 2
    scores['correctness'] = (scores['f1_score'] + scores['precision']) / 2
    return {'results': [{'key': key, 'score': value} for key, value in scores.items()]}


def summarize(rows):
    """Não aprova média baseada em subconjunto nem feedback ausente."""
    if len(rows) != 15:
        raise ValueError('Experimento deve conter exatamente 15 resultados.')
    totals = {name: [] for name in METRICS}
    for row in rows:
        run = row['run']
        if run.error or not (run.outputs or {}).get('answer'):
            raise ValueError('Há execução sem resposta.')
        feedback = {item.key: item.score for item in row['evaluation_results']['results']}
        for name in METRICS:
            score = feedback.get(name)
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError(f'Feedback inválido ou ausente: {name}')
            totals[name].append(score)
    scores = {name: sum(values)/15 for name, values in totals.items()}
    return {'examples': 15, 'scores': scores, 'average': sum(scores.values())/5,
            'passed': all(value >= 0.8 for value in scores.values()),
            'run_ids': [str(row['run'].id) for row in rows]}


def run_experiment(prompt_ref, version, client, dataset_name):
    source = ROOT / 'datasets/bug_to_user_story.jsonl'
    examples = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    if len(examples) != 15:
        raise ValueError('Dataset local deve ter 15 exemplos.')
    # Nome único por execução evita reutilizar dataset remoto antigo ou adulterado.
    dataset = client.create_dataset(dataset_name=dataset_name)
    client.create_examples(inputs=[x['inputs'] for x in examples],
                           outputs=[x['outputs'] for x in examples], dataset_id=dataset.id)
    prompt = hub.pull(prompt_ref)
    chain = prompt | get_llm(temperature=0)

    def predict(inputs):
        response = chain.invoke(inputs)
        if not isinstance(response.content, str) or not response.content.strip():
            raise ValueError('Modelo não retornou texto.')
        return {'answer': response.content}

    experiment = evaluate(predict, data=dataset_name, evaluators=[grade], client=client,
                          max_concurrency=1, experiment_prefix=f'bug-user-story-{version}',
                          metadata={'prompt_ref': prompt_ref,
                                    'hub_commit': (prompt.metadata or {}).get('lc_hub_commit_hash'),
                                    'dataset_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                                    'llm_model': os.getenv('LLM_MODEL'), 'eval_model': os.getenv('EVAL_MODEL')})
    report = summarize(list(experiment))
    report.update({'prompt_ref': prompt_ref,
                   'hub_commit': (prompt.metadata or {}).get('lc_hub_commit_hash'),
                   'experiment_name': experiment.experiment_name,
                   'dataset_name': dataset_name,
                   'dataset_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                   'llm_model': os.getenv('LLM_MODEL'), 'eval_model': os.getenv('EVAL_MODEL'),
                   'created_at': datetime.now(timezone.utc).isoformat()})
    project = client.read_project(project_name=experiment.experiment_name)
    report['dashboard_url'] = project.url
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True, choices=('v1','v2'))
    parser.add_argument('--prompt-ref', help='owner/name:commit para reprodutibilidade')
    args = parser.parse_args(argv)
    provider = os.getenv('LLM_PROVIDER')
    if provider not in ('openai', 'google'):
        print('Configure LLM_PROVIDER=openai ou google.'); return 1
    required = ['LANGSMITH_API_KEY','LANGSMITH_PROJECT','LLM_MODEL','EVAL_MODEL',
                'OPENAI_API_KEY' if provider=='openai' else 'GOOGLE_API_KEY']
    if args.version == 'v2' and not args.prompt_ref:
        required.append('USERNAME_LANGSMITH_HUB')
    if not check_env_vars(required):
        return 1
    prompt_ref = args.prompt_ref or ('leonanluppi/bug_to_user_story_v1' if args.version=='v1'
                                    else os.environ['USERNAME_LANGSMITH_HUB']+'/bug_to_user_story_v2')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    try:
        report = run_experiment(prompt_ref,args.version,Client(),f"{os.environ['LANGSMITH_PROJECT']}-{args.version}-{stamp}")
        output = ROOT / 'results' / f'{args.version}-{stamp}.json'
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(f'Relatório: {output.name}')
        print(f"Dashboard: {report['dashboard_url']}")
        print(json.dumps(report['scores'],indent=2))
        return 0 if report['passed'] else 1
    except Exception as error:
        print(f'Experimento não concluído ({type(error).__name__}). Confira dashboard e credenciais; nenhuma aprovação registrada.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
