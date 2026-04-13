import base64
import json
from pathlib import Path
import pytest
from unittest.mock import Mock

from client.langfuse_metrics_client import LangfuseMetricsClient


def load_env(dotenv_path: Path):
    env_vars = {}
    if not dotenv_path.exists():
        return env_vars

    for line in dotenv_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


class TestLangfuseMetricsClient:
    @pytest.fixture
    def env_vars(self):
        root = Path(__file__).resolve().parents[1]
        return load_env(root / '.env')

    @pytest.fixture
    def client(self, env_vars):
        return LangfuseMetricsClient(
            public_key=env_vars.get('LANGFUSE_PUBLIC_KEY', 'pk-test'),
            secret_key=env_vars.get('LANGFUSE_SECRET_KEY', 'sk-test'),
            base_url=env_vars.get('LANGFUSE_BASE_URL', 'https://example.com')
        )

    def test_init(self, client, env_vars):
        assert client.public_key == env_vars.get('LANGFUSE_PUBLIC_KEY', 'pk-test')
        assert client.secret_key == env_vars.get('LANGFUSE_SECRET_KEY', 'sk-test')
        assert client.base_url == env_vars.get('LANGFUSE_BASE_URL', 'https://example.com')

    def test_get_headers(self, client, env_vars):
        headers = client._get_headers()

        assert 'Authorization' in headers
        assert headers['Authorization'].startswith('Basic ')

        encoded_creds = headers['Authorization'].split(' ')[1]
        decoded_creds = base64.b64decode(encoded_creds).decode()
        expected_creds = f"{env_vars.get('LANGFUSE_PUBLIC_KEY', 'pk-test')}:{env_vars.get('LANGFUSE_SECRET_KEY', 'sk-test')}"
        assert decoded_creds == expected_creds

    def test_get_metrics_success(self, client, monkeypatch):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'data': [{'count': 10}]}

        def fake_get(url, headers=None, params=None):
            assert url == f"{client.base_url}/api/public/v2/metrics"
            assert headers is not None
            assert headers['Authorization'].startswith('Basic ')
            assert params == {
                'query': json.dumps({
                    'view': 'observations',
                    'metrics': [{'measure': 'count', 'aggregation': 'sum'}],
                    'fromTimestamp': '2024-01-01T00:00:00Z',
                    'toTimestamp': '2024-12-31T23:59:59Z'
                })
            }
            return mock_response

        monkeypatch.setattr('requests.get', fake_get)

        query = {
            'view': 'observations',
            'metrics': [{'measure': 'count', 'aggregation': 'sum'}],
            'fromTimestamp': '2024-01-01T00:00:00Z',
            'toTimestamp': '2024-12-31T23:59:59Z'
        }

        result = client.get_metrics(query)

        assert result == {'data': [{'count': 10}]}
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()

    def test_get_metrics_request_failure(self, client, monkeypatch):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception('Request failed')

        def fake_get(url, headers=None, params=None):
            assert url == f"{client.base_url}/api/public/v2/metrics"
            assert headers is not None
            assert headers['Authorization'].startswith('Basic ')
            assert params == {
                'query': json.dumps({
                    'view': 'observations',
                    'metrics': [{'measure': 'count'}]
                })
            }
            return mock_response

        monkeypatch.setattr('requests.get', fake_get)

        query = {'view': 'observations', 'metrics': [{'measure': 'count'}]}

        with pytest.raises(Exception, match='Request failed'):
            client.get_metrics(query)