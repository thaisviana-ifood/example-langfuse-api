import base64
import json
import requests


class LangfuseMetricsClient:
    def __init__(self, public_key, secret_key, base_url):
        self.public_key = public_key
        self.secret_key = secret_key
        self.base_url = base_url

    def _get_headers(self):
        credentials = f"{self.public_key}:{self.secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    def get_metrics(self, query):
        """
        Retrieve metrics from Langfuse API v2.
        
        Args:
            query (dict): Query parameters for the metrics API v2
            
        Returns:
            dict: JSON response from the API
        """
        url = f"{self.base_url}/api/public/v2/metrics"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        payload = {"query": query}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()