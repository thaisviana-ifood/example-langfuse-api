import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from client.langfuse_metrics_client import LangfuseMetricsClient

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / '.env')

PUBLIC_KEY = os.getenv('LANGFUSE_PUBLIC_KEY')
SECRET_KEY = os.getenv('LANGFUSE_SECRET_KEY')
BASE_URL = os.getenv('LANGFUSE_BASE_URL')

if not PUBLIC_KEY or not SECRET_KEY or not BASE_URL:
    raise RuntimeError(
        'Missing Langfuse configuration. Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY and LANGFUSE_BASE_URL in .env or environment.'
    )

client = LangfuseMetricsClient(
    public_key=PUBLIC_KEY,
    secret_key=SECRET_KEY,
    base_url=BASE_URL,
)

app = Flask(__name__, static_folder='dashboard', static_url_path='')

@app.route('/api/metrics', methods=['POST'])
def metrics_proxy():
    payload = request.get_json(silent=True)
    if not payload or 'query' not in payload:
        return jsonify({'error': 'O corpo da requisição deve incluir o campo `query`.'}), 400

    query = payload['query']
    try:
        result = client.get_metrics(query)
        return jsonify(result)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_dashboard(path):
    dashboard_dir = ROOT_DIR / 'dashboard'
    if not (dashboard_dir / path).exists():
        return send_from_directory(str(dashboard_dir), 'index.html')
    return send_from_directory(str(dashboard_dir), path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
