import { useCallback, useEffect, useState } from 'react';
import type {
  CreateTicketInput,
  Ticket,
  TicketEvent,
  TicketStatus,
  UpdateTicketInput,
} from '@tickethub/shared';
import { ticketsApi } from '../api/ticketsApi';

interface UseTicketsResult {
  tickets: Ticket[];
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  createTicket: (input: CreateTicketInput) => Promise<void>;
  changeStatus: (id: number, status: TicketStatus, reviewNote?: string) => Promise<void>;
  updateTicket: (id: number, input: UpdateTicketInput) => Promise<void>;
  getEvents: (id: number) => Promise<TicketEvent[]>;
}

export function useTickets(): UseTicketsResult {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
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
    // Aggiorna periodicamente la board (il job gira in background ogni minuto).
    const timer = setInterval(() => void reload(), 15000);
    return () => clearInterval(timer);
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

  const updateTicket = useCallback(
    async (id: number, input: UpdateTicketInput) => {
      await ticketsApi.update(id, input);
      await reload();
    },
    [reload],
  );

  const getEvents = useCallback((id: number) => ticketsApi.events(id), []);

  return {
    tickets,
    loading,
    error,
    reload,
    createTicket,
    changeStatus,
    updateTicket,
    getEvents,
  };
}
