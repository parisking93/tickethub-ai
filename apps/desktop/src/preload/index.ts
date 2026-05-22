import { contextBridge } from 'electron';

/**
 * Legge l'URL del backend passato dal main process come argomento del renderer
 * (--backend-url=...). È il metodo affidabile in app impacchettata, dove le
 * modifiche a process.env fatte dal main a runtime non arrivano al preload.
 */
function readBackendUrl(): string {
  const prefix = '--backend-url=';
  const arg = process.argv.find((a) => a.startsWith(prefix));
  if (arg) return arg.slice(prefix.length);
  return process.env.BACKEND_URL ?? 'http://127.0.0.1:8000';
}

const api = {
  backendUrl: readBackendUrl(),
};

contextBridge.exposeInMainWorld('tam', api);

export type TamApi = typeof api;
