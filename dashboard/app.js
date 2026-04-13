const form = document.getElementById('metrics-form');
const result = document.getElementById('result');
const debug = document.getElementById('debug');

const buildQuery = () => {
  const view = document.getElementById('view').value;
  const measure = document.getElementById('metric').value;
  const aggregation = document.getElementById('aggregation').value;
  const from = document.getElementById('fromTimestamp').value;
  const to = document.getElementById('toTimestamp').value;

  return {
    view,
    dimensions: [],
    metrics: [{ measure, aggregation }],
    fromTimestamp: new Date(from).toISOString(),
    toTimestamp: new Date(to).toISOString(),
  };
};

const renderResult = (data) => {
  if (!data) {
    result.textContent = 'Resposta vazia';
    return;
  }

  try {
    const json = JSON.stringify(data, null, 2);
    result.textContent = json;
  } catch (error) {
    result.textContent = String(data);
  }
};

const renderDebug = (message) => {
  debug.textContent = typeof message === 'string' ? message : JSON.stringify(message, null, 2);
};

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  result.textContent = 'Carregando...';
  debug.textContent = '';

  const query = buildQuery();

  try {
    const response = await fetch('/api/metrics', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    const body = await response.json();

    if (!response.ok) {
      renderResult('Erro ao buscar métricas');
      renderDebug(body);
      return;
    }

    renderResult(body);
    renderDebug({ status: response.status, query });
  } catch (error) {
    renderResult('Falha na requisição');
    renderDebug(error.message || error);
  }
});
