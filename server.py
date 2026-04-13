import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from client.langfuse_metrics_client import LangfuseMetricsClient

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / '.env')

BASE_URL = os.getenv('LANGFUSE_BASE_URL')
ORG = os.getenv('LANGFUSE_ORG')
PROJECTS_STR = os.getenv('LANGFUSE_PROJECTS', '')

if not BASE_URL:
    raise RuntimeError('Missing LANGFUSE_BASE_URL in .env')

projects = [p.strip() for p in PROJECTS_STR.split(',') if p.strip()]
clients = {}

for project in projects:
    pk_key = f'LANGFUSE_PUBLIC_KEY_{project}' if len(projects) > 1 else 'LANGFUSE_PUBLIC_KEY'
    sk_key = f'LANGFUSE_SECRET_KEY_{project}' if len(projects) > 1 else 'LANGFUSE_SECRET_KEY'
    
    public_key = os.getenv(pk_key)
    secret_key = os.getenv(sk_key)
    
    if not public_key or not secret_key:
        raise RuntimeError(f'Missing keys for project {project}')
    
    clients[project] = LangfuseMetricsClient(
        public_key=public_key,
        secret_key=secret_key,
        base_url=BASE_URL,
    )

default_project = projects[0] if projects else None

app = Flask(__name__, static_folder='dashboard', static_url_path='')

@app.route('/api/metrics', methods=['POST'])
def metrics_proxy():
    payload = request.get_json(silent=True)
    if not payload or 'query' not in payload:
        return jsonify({'error': 'O corpo da requisição deve incluir o campo `query`.'}), 400

    project = payload.get('project', default_project)
    if project not in clients:
        return jsonify({'error': f'Projeto {project} não configurado.'}), 400

    query = payload['query']
    try:
        result = clients[project].get_metrics(query)
        return jsonify(result)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

@app.route('/api/info', methods=['GET'])
def info():
    return jsonify({
        'org': ORG,
        'projects': projects,
        'default_project': default_project
    })

@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_dashboard(path):
    dashboard_dir = ROOT_DIR / 'dashboard'
    if not (dashboard_dir / path).exists():
        return send_from_directory(str(dashboard_dir), 'index.html')
    return send_from_directory(str(dashboard_dir), path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
