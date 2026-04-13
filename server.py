import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from client.langfuse_metrics_client import LangfuseMetricsClient

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / '.env')

BASE_URL = os.getenv('LANGFUSE_BASE_URL')
ORG = os.getenv('LANGFUSE_ORG')
ORG_PUBLIC_KEY = os.getenv('LANGFUSE_ORG_PUBLIC_KEY')
ORG_SECRET_KEY = os.getenv('LANGFUSE_ORG_SECRET_KEY')

if not BASE_URL:
    raise RuntimeError('Missing LANGFUSE_BASE_URL in .env')

def get_org_projects():
    if not ORG_PUBLIC_KEY or not ORG_SECRET_KEY:
        # Fallback to configured projects
        projects_str = os.getenv('LANGFUSE_PROJECTS', '')
        return [p.strip() for p in projects_str.split(',') if p.strip()]
    
    # Fetch from Langfuse API
    import requests
    url = f"{BASE_URL}/api/public/organizations/projects"
    credentials = f"{ORG_PUBLIC_KEY}:{ORG_SECRET_KEY}"
    encoded = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {encoded}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return [p['name'] for p in data.get('projects', [])]
    except Exception as e:
        print(f"Failed to fetch projects from Langfuse: {e}")
        # Fallback
        projects_str = os.getenv('LANGFUSE_PROJECTS', '')
        return [p.strip() for p in projects_str.split(',') if p.strip()]

projects = get_org_projects()
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
    
    if project == 'all':
        combined_data = []
        errors = []
        for proj, client in clients.items():
            try:
                result = client.get_metrics(payload['query'])
                # Add project info to each data item
                if 'data' in result and isinstance(result['data'], list):
                    for item in result['data']:
                        item['_project'] = proj
                    combined_data.extend(result['data'])
            except Exception as exc:
                errors.append(f'{proj}: {str(exc)}')
                combined_data.append({"_project": proj, "sum_count": "0"})
        
        combined_result = {'data': combined_data}
        if errors:
            combined_result['warnings'] = errors
        
        return jsonify(combined_result)
    
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
    available_projects = projects + ['all']
    return jsonify({
        'org': ORG,
        'projects': available_projects,
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
