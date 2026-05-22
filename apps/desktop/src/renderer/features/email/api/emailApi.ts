import type { CreateEmailAccountInput, EmailAccount, EmailSyncResult } from '@tickethub/shared';

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

export const emailApi = {
  listAccounts: (): Promise<EmailAccount[]> => request<EmailAccount[]>('/email/accounts'),

  createAccount: (input: CreateEmailAccountInput): Promise<EmailAccount> =>
    request<EmailAccount>('/email/accounts', { method: 'POST', body: JSON.stringify(input) }),

  deleteAccount: (id: number): Promise<void> =>
    request<void>(`/email/accounts/${id}`, { method: 'DELETE' }),

  startOAuth: (id: number): Promise<{ authorize_url: string }> =>
    request<{ authorize_url: string }>(`/email/accounts/${id}/oauth/start`, { method: 'POST' }),

  sync: (accountId?: number): Promise<EmailSyncResult[]> =>
    request<EmailSyncResult[]>(
      accountId ? `/email/sync?account_id=${accountId}` : '/email/sync',
      { method: 'POST' },
    ),
};
