# example-langfuse-api

Exemplo de consumo da API pública do Langfuse usando Python.

## Overview

Este repositório contém um cliente simples para a API de métricas do Langfuse.
A implementação está em `client/langfuse_metrics_client.py` e fornece:

- autenticação Basic Auth usando `public_key` e `secret_key`
- requisição ao endpoint `/api/public/v2/metrics`
- serialização correta do corpo `query` como JSON

## Estrutura

- `client/langfuse_metrics_client.py` — classe `LangfuseMetricsClient`
- `tests/test_langfuse_metrics_client.py` — testes unitários com `pytest`
- `.env` — variáveis de ambiente para as chaves e `base_url`
- `requirements.txt` — dependências do projeto

## Configuração

1. Crie e ative um ambiente Python:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure o arquivo `.env` com seus valores:

```env
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"
```

## Uso

Exemplo de uso do cliente:

```python
from client.langfuse_metrics_client import LangfuseMetricsClient

client = LangfuseMetricsClient(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    base_url="https://us.cloud.langfuse.com",
)

query = {
    "view": "observations",
    "metrics": [{"measure": "count", "aggregation": "sum"}],
    "fromTimestamp": "2024-01-01T00:00:00Z",
    "toTimestamp": "2024-12-31T23:59:59Z",
}

result = client.get_metrics(query)
print(result)
```

## Testes

Execute os testes com:

```bash
pytest tests/test_langfuse_metrics_client.py -v
```

## Observações

- A autenticação do Langfuse usa o `public_key` como username e o `secret_key` como password em Basic Auth.
- A classe gera o header `Authorization` corretamente e dispatcha a query como JSON no parâmetro `query`.
