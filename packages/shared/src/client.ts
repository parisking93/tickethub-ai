/**
 * Client API condiviso tra desktop (Electron) e mobile (React Native).
 * Usa `fetch` (globale su entrambe le piattaforme). Nessuna dipendenza di piattaforma.
 */

import type {
  CreateEmailAccountInput,
  EmailAccount,
  EmailSyncResult,
} from './email';
import type { CreateOdooConnectionInput, OdooConnection, OdooSyncResult } from './odoo';
import type { CreateProjectInput, Project } from './project';
import type {
  Attachment,
  CreateTicketInput,
  JobRunResult,
  Ticket,
  TicketEvent,
  TicketMessage,
  TicketStatus,
  UpdateTicketInput,
  UpdateTicketStatusInput,
} from './ticket';

export type BaseUrl = string | (() => string);

export function createApiClient(baseUrl: BaseUrl) {
  const resolve = typeof baseUrl === 'function' ? baseUrl : (): string => baseUrl;

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${resolve()}/api/v1${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error((detail as { detail?: string }).detail ?? `Errore ${res.status}`);
    }
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  }

  const body = (data: unknown): string => JSON.stringify(data);

  return {
    request,

    tickets: {
      list: (status?: TicketStatus): Promise<Ticket[]> =>
        request<Ticket[]>(status ? `/tickets?status=${status}` : '/tickets'),
      get: (id: number): Promise<Ticket> => request<Ticket>(`/tickets/${id}`),
      events: (id: number): Promise<TicketEvent[]> =>
        request<TicketEvent[]>(`/tickets/${id}/events`),
      messages: (id: number): Promise<TicketMessage[]> =>
        request<TicketMessage[]>(`/tickets/${id}/messages`),
      attachments: (id: number): Promise<Attachment[]> =>
        request<Attachment[]>(`/tickets/${id}/attachments`),
      uploadAttachment: async (id: number, file: File): Promise<Attachment> => {
        const form = new FormData();
        form.append('file', file);
        const res = await fetch(`${resolve()}/api/v1/tickets/${id}/attachments`, {
          method: 'POST',
          body: form,
        });
        if (!res.ok) {
          const detail = await res.json().catch(() => ({}));
          throw new Error((detail as { detail?: string }).detail ?? `Errore ${res.status}`);
        }
        return (await res.json()) as Attachment;
      },
      attachmentUrl: (id: number, attachmentId: number): string =>
        `${resolve()}/api/v1/tickets/${id}/attachments/${attachmentId}/download`,
      create: (input: CreateTicketInput): Promise<Ticket> =>
        request<Ticket>('/tickets', { method: 'POST', body: body(input) }),
      update: (id: number, input: UpdateTicketInput): Promise<Ticket> =>
        request<Ticket>(`/tickets/${id}`, { method: 'PATCH', body: body(input) }),
      updateStatus: (id: number, input: UpdateTicketStatusInput): Promise<Ticket> =>
        request<Ticket>(`/tickets/${id}/status`, { method: 'PATCH', body: body(input) }),
    },

    worker: {
      run: (): Promise<JobRunResult> => request<JobRunResult>('/worker/run', { method: 'POST' }),
      processTicket: (id: number): Promise<unknown> =>
        request(`/worker/tickets/${id}/process`, { method: 'POST' }),
    },

    email: {
      listAccounts: (): Promise<EmailAccount[]> => request<EmailAccount[]>('/email/accounts'),
      createAccount: (input: CreateEmailAccountInput): Promise<EmailAccount> =>
        request<EmailAccount>('/email/accounts', { method: 'POST', body: body(input) }),
      deleteAccount: (id: number): Promise<void> =>
        request<void>(`/email/accounts/${id}`, { method: 'DELETE' }),
      startOAuth: (id: number): Promise<{ authorize_url: string }> =>
        request<{ authorize_url: string }>(`/email/accounts/${id}/oauth/start`, {
          method: 'POST',
        }),
      sync: (accountId?: number): Promise<EmailSyncResult[]> =>
        request<EmailSyncResult[]>(
          accountId ? `/email/sync?account_id=${accountId}` : '/email/sync',
          { method: 'POST' },
        ),
    },

    projects: {
      list: (): Promise<Project[]> => request<Project[]>('/projects'),
      create: (input: CreateProjectInput): Promise<Project> =>
        request<Project>('/projects', { method: 'POST', body: body(input) }),
      remove: (id: number): Promise<void> =>
        request<void>(`/projects/${id}`, { method: 'DELETE' }),
    },

    odoo: {
      listConnections: (): Promise<OdooConnection[]> =>
        request<OdooConnection[]>('/odoo/connections'),
      createConnection: (input: CreateOdooConnectionInput): Promise<OdooConnection> =>
        request<OdooConnection>('/odoo/connections', { method: 'POST', body: body(input) }),
      deleteConnection: (id: number): Promise<void> =>
        request<void>(`/odoo/connections/${id}`, { method: 'DELETE' }),
      sync: (connectionId?: number): Promise<OdooSyncResult[]> =>
        request<OdooSyncResult[]>(
          connectionId ? `/odoo/sync?connection_id=${connectionId}` : '/odoo/sync',
          { method: 'POST' },
        ),
    },
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
