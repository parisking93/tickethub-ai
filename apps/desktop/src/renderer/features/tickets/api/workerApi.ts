import type { JobRunResult } from '@tickethub/shared';

const baseUrl = (): string => window.tam?.backendUrl ?? 'http://127.0.0.1:8000';

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${baseUrl()}/api/v1${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Errore ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const workerApi = {
  /** Esegue un giro del job: finalizza gli approvati e lavora i nuovi/rifiutati. */
  run: (): Promise<JobRunResult> => post<JobRunResult>('/worker/run'),

  /** Elabora un singolo ticket con l'AI. */
  processTicket: (id: number): Promise<unknown> => post(`/worker/tickets/${id}/process`),
};
