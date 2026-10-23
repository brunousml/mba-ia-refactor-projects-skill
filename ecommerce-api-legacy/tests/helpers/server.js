// Sobe a aplicação como processo filho (o entry point original chama listen ao ser carregado).
// Cada chamada parte de um banco novo, porque o SQLite é em memória e o seed roda no boot.
// A porta é efêmera (o SO escolhe uma livre a cada boot); a suíte segue com --test-concurrency=1.
const { spawn } = require('node:child_process');
const net = require('node:net');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..', '..');
const ADMIN_TOKEN = 'test-admin-token';

// Ambiente que reproduz o comportamento original nas rotas guardadas pelo T08.
const FLAGS_ON = {
  ENABLE_ADMIN_ROUTES: 'true',
  ENABLE_SENSITIVE_READS: 'true',
  ENABLE_WRITE_ROUTES: 'true',
  ADMIN_TOKEN,
};

function freePort() {
  return new Promise((resolve, reject) => {
    const probe = net.createServer();
    probe.once('error', reject);
    probe.listen(0, '127.0.0.1', () => {
      const { port } = probe.address();
      probe.close(() => resolve(port));
    });
  });
}

async function startServer(env = FLAGS_ON) {
  const PORT = await freePort();
  const child = spawn(process.execPath, ['src/app.js'], {
    cwd: ROOT,
    env: { PATH: process.env.PATH, PORT: String(PORT), ...env },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let output = '';
  child.stdout.on('data', (d) => { output += d; });
  child.stderr.on('data', (d) => { output += d; });

  const base = `http://127.0.0.1:${PORT}`;
  for (let i = 0; i < 100; i++) {
    if (child.exitCode !== null) throw new Error(`app saiu no boot:\n${output}`);
    try { await fetch(base + '/'); break; } catch { await new Promise((r) => setTimeout(r, 100)); }
  }

  async function request(method, urlPath, { body, headers = {} } = {}) {
    const res = await fetch(base + urlPath, {
      method,
      headers: { 'Content-Type': 'application/json', ...headers },
      body: body === undefined ? undefined : (typeof body === 'string' ? body : JSON.stringify(body)),
    });
    const text = await res.text();
    let json;
    try { json = JSON.parse(text); } catch { json = undefined; }
    return { status: res.status, text, json };
  }

  async function stop() {
    if (child.exitCode !== null) return;
    child.kill();
    await new Promise((r) => child.once('exit', r));
  }

  return { base, request, stop, logs: () => output, alive: () => child.exitCode === null };
}

module.exports = { startServer, FLAGS_ON, ADMIN_TOKEN, AUTH: { 'X-Admin-Token': ADMIN_TOKEN } };
