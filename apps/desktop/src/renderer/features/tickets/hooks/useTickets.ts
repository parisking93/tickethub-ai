import { useCallback, useEffect, useState } from 'react';
import type { CreateTicketInput, Ticket, TicketStatus } from '@tickethub/shared';
import { ticketsApi } from '../api/ticketsApi';

interface UseTicketsResult {
  tickets: Ticket[];
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  createTicket: (input: CreateTicketInput) => Promise<void>;
  changeStatus: (id: number, status: TicketStatus, reviewNote?: string) => Promise<void>;
}

export function useTickets(): UseTicketsResult {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setTickets(await ticketsApi.list());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore di caricamento');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const createTicket = useCallback(
    async (input: CreateTicketInput) => {
      await ticketsApi.create(input);
      await reload();
    },
    [reload],
  );

  const changeStatus = useCallback(
    async (id: number, status: TicketStatus, reviewNote?: string) => {
      await ticketsApi.updateStatus(id, { status, review_note: reviewNote });
      await reload();
    },
    [reload],
  );

  return { tickets, loading, error, reload, createTicket, changeStatus };
}
