import { contextBridge } from 'electron';

/**
 * API esposta in modo sicuro al renderer tramite contextBridge.
 * Per ora espone solo l'URL del backend; in futuro qui passeranno
 * eventuali invocazioni IPC verso il main process.
 */
const api = {
  backendUrl: process.env.BACKEND_URL ?? 'http://127.0.0.1:8000',
};

contextBridge.exposeInMainWorld('tam', api);

export type TamApi = typeof api;
