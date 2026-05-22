import { spawn, type ChildProcess } from 'node:child_process';
import { createServer } from 'node:net';
import { join } from 'node:path';
import { existsSync } from 'node:fs';
import { app } from 'electron';

let backendProcess: ChildProcess | null = null;

/** Trova una porta TCP libera su localhost. */
function getFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.unref();
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const address = server.address();
      const port = typeof address === 'object' && address ? address.port : 0;
      server.close(() => resolve(port));
    });
  });
}

interface BackendCommand {
  command: string;
  args: string[];
  cwd: string;
}

/**
 * Determina come avviare il backend:
 * - pacchetto: eseguibile bundlato in resources/backend/.
 * - sviluppo: Python del venv + uvicorn sul codice sorgente.
 */
function resolveCommand(): BackendCommand {
  if (app.isPackaged) {
    const exe = join(process.resourcesPath, 'backend', 'tickethub-backend.exe');
    return { command: exe, args: [], cwd: join(process.resourcesPath, 'backend') };
  }
  // Sviluppo: repoRoot = <repo>, da apps/desktop risaliamo di due livelli.
  const repoRoot = join(app.getAppPath(), '..', '..');
  const backendDir = join(repoRoot, 'backend');
  const venvPython = join(backendDir, '.venv', 'Scripts', 'python.exe');
  return {
    command: venvPython,
    args: ['-m', 'uvicorn', 'app.main:app', '--app-dir', join(backendDir, 'src')],
    cwd: backendDir,
  };
}

async function waitForHealth(baseUrl: string, timeoutMs = 30000): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${baseUrl}/health`);
      if (res.ok) return true;
    } catch {
      // backend non ancora pronto
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

/**
 * Avvia il backend e attende che risponda. Ritorna l'URL base.
 * Imposta BACKEND_URL nell'ambiente così il preload lo espone al renderer.
 */
export async function startBackend(): Promise<string> {
  const port = await getFreePort();
  const baseUrl = `http://127.0.0.1:${port}`;
  const { command, args, cwd } = resolveCommand();

  if (!existsSync(command)) {
    console.error(`[backend] eseguibile non trovato: ${command}`);
    process.env.BACKEND_URL = baseUrl;
    return baseUrl;
  }

  const dbPath = join(app.getPath('userData'), 'tickethub.sqlite3').replace(/\\/g, '/');
  backendProcess = spawn(command, args, {
    cwd,
    env: {
      ...process.env,
      API_HOST: '127.0.0.1',
      PORT: String(port),
      DATABASE_URL: `sqlite:///${dbPath}`,
      AI_PROVIDER: process.env.AI_PROVIDER ?? 'ollama',
      AI_MODEL: process.env.AI_MODEL ?? 'gpt-oss:20b',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  backendProcess.stdout?.on('data', (d) => console.log(`[backend] ${d.toString().trim()}`));
  backendProcess.stderr?.on('data', (d) => console.log(`[backend] ${d.toString().trim()}`));
  backendProcess.on('exit', (code) => console.log(`[backend] terminato (code ${code})`));

  const healthy = await waitForHealth(baseUrl);
  if (!healthy) console.error('[backend] non ha risposto entro il timeout');

  process.env.BACKEND_URL = baseUrl;
  return baseUrl;
}

/** Arresta il backend (chiamato alla chiusura dell'app). */
export function stopBackend(): void {
  if (!backendProcess || backendProcess.killed) return;
  const pid = backendProcess.pid;
  backendProcess = null;
  if (pid === undefined) return;
  if (process.platform === 'win32') {
    // Termina l'intero albero del processo su Windows.
    spawn('taskkill', ['/pid', String(pid), '/T', '/F'], { stdio: 'ignore' });
  } else {
    try {
      process.kill(pid);
    } catch {
      // già terminato
    }
  }
}
