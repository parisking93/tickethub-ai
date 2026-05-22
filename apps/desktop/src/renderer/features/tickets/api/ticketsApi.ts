import type {
  CreateTicketInput,
  Ticket,
  TicketStatus,
  UpdateTicketStatusInput,
} from '@tickethub/shared';

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
  return res.json() as Promise<T>;
}

export const ticketsApi = {
  list: (status?: TicketStatus): Promise<Ticket[]> =>
    request<Ticket[]>(status ? `/tickets?status=${status}` : '/tickets'),

  create: (input: CreateTicketInput): Promise<Ticket> =>
    request<Ticket>('/tickets', { method: 'POST', body: JSON.stringify(input) }),

  updateStatus: (id: number, input: UpdateTicketStatusInput): Promise<Ticket> =>
    request<Ticket>(`/tickets/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    }),
};
