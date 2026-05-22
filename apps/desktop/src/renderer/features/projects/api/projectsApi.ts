import type { CreateProjectInput, Project } from '@tickethub/shared';

const baseUrl = (): string => window.tam?.backendUrl ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl()}/api/v1${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Errore ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const projectsApi = {
  list: (): Promise<Project[]> => request<Project[]>('/projects'),

  create: (input: CreateProjectInput): Promise<Project> =>
    request<Project>('/projects', { method: 'POST', body: JSON.stringify(input) }),

  remove: (id: number): Promise<void> =>
    request<void>(`/projects/${id}`, { method: 'DELETE' }),
};
