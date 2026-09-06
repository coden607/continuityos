const apiInput = document.querySelector('#api-base');
const healthBadge = document.querySelector('#health-badge');
const healthDetail = document.querySelector('#health-detail');
const result = document.querySelector('#result');
const networkState = document.querySelector('#network-state');
const form = document.querySelector('#execute-form');
const capability = document.querySelector('#capability');
const prompt = document.querySelector('#prompt');

const defaultApiBase = `${location.protocol === 'file:' ? 'http:' : location.protocol}//${location.hostname || '127.0.0.1'}:8000`;
apiInput.value = localStorage.getItem('continuity.apiBase') || defaultApiBase;

function apiUrl(path) {
  return `${apiInput.value.replace(/\/$/, '')}${path}`;
}

function setHealth(status, detail = '') {
  healthBadge.textContent = status;
  healthBadge.dataset.state = status;
  healthDetail.textContent = detail || `Runtime is ${status}.`;
}

async function refreshHealth() {
  try {
    const response = await fetch(apiUrl('/status/health'), { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const body = await response.json();
    setHealth(body.status || 'healthy', 'Connected to ContinuityOS API.');
  } catch (error) {
    setHealth('offline', `API unavailable: ${error.message}`);
  }
}

async function executeTask(event) {
  event.preventDefault();
  result.textContent = 'Executing…';
  try {
    const response = await fetch(apiUrl('/execute'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ task_id: crypto.randomUUID(), prompt: prompt.value, capability: capability.value }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
    result.textContent = JSON.stringify(body, null, 2);
  } catch (error) {
    result.textContent = `Execution failed: ${error.message}`;
  }
}

function updateNetwork() {
  networkState.textContent = navigator.onLine ? 'online' : 'offline';
}

document.querySelector('#save-api').addEventListener('click', () => {
  localStorage.setItem('continuity.apiBase', apiInput.value.trim());
  refreshHealth();
});
form.addEventListener('submit', executeTask);
window.addEventListener('online', () => { updateNetwork(); refreshHealth(); });
window.addEventListener('offline', updateNetwork);

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('./service-worker.js').catch(() => {});
}

updateNetwork();
refreshHealth();
