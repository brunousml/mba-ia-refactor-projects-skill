// Sobe a aplicação como processo filho numa porta livre (o entry point chama listen ao ser carregado).
// Cada chamada a startServer cria um processo novo e, portanto, um banco em memória recém-semeado.
const { spawn } = require('node:child_process');
const net = require('node:net');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..', '..');
const ADMIN_TOKEN = 'test-admin-token';

// Flags do T08 ligadas: as rotas voltam ao comportamento original quando o token é enviado.
const FLAGS_ON = {
    ENABLE_ADMIN_ROUTES: 'true',
    ENABLE_SENSITIVE_READS: 'true',
    ENABLE_WRITE_ROUTES: 'true',
    ADMIN_TOKEN,
};
const FLAGS_OFF = {
    ENABLE_ADMIN_ROUTES: 'false',
    ENABLE_SENSITIVE_READS: 'false',
    ENABLE_WRITE_ROUTES: 'false',
    ADMIN_TOKEN,
};

function freePort() {
    return new Promise((resolve, reject) => {
        const srv = net.createServer();
        srv.unref();
        srv.on('error', reject);
        srv.listen(0, '127.0.0.1', () => {
            const { port } = srv.address();
            srv.close(() => resolve(port));
        });
    });
}

async function startServer(env = FLAGS_ON) {
    const port = await freePort();
    const child = spawn(process.execPath, ['src/app.js'], {
        cwd: ROOT,
        env: { ...process.env, ...env, PORT: String(port) },
        stdio: ['ignore', 'pipe', 'pipe'],
    });
    const server = { port, child, logs: '', exited: false };
    child.stdout.on('data', (d) => { server.logs += d; });
    child.stderr.on('data', (d) => { server.logs += d; });
    child.on('exit', () => { server.exited = true; });

    const base = `http://127.0.0.1:${port}`;
    for (let i = 0; i < 100; i++) {
        if (server.exited) throw new Error(`Aplicação encerrou no boot:\n${server.logs}`);
        try { await fetch(base + '/'); break; } catch { await new Promise((r) => setTimeout(r, 50)); }
    }

    server.base = base;
    // request(method, path, { body, token }) -> { status, text, json, headers }
    server.request = async (method, urlPath, { body, token = ADMIN_TOKEN, headers = {} } = {}) => {
        const h = { ...headers };
        if (token) h['X-Admin-Token'] = token;
        if (body !== undefined) h['Content-Type'] = 'application/json';
        const res = await fetch(base + urlPath, {
            method,
            headers: h,
            body: body !== undefined ? JSON.stringify(body) : undefined,
        });
        const text = await res.text();
        let json;
        try { json = JSON.parse(text); } catch { json = undefined; }
        return { status: res.status, text, json, headers: res.headers };
    };
    server.stop = () => new Promise((resolve) => {
        if (server.exited) return resolve();
        child.once('exit', resolve);
        child.kill();
    });
    return server;
}

module.exports = { startServer, FLAGS_ON, FLAGS_OFF, ADMIN_TOKEN };
