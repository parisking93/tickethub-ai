import { useTickets } from '../features/tickets/hooks/useTickets';
import { TicketBoard } from '../features/tickets/components/TicketBoard';
import { CreateTicketForm } from '../features/tickets/components/CreateTicketForm';

export function App(): JSX.Element {
  const { tickets, loading, error, reload, createTicket, changeStatus } = useTickets();

  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">Ticket AI Manager</h1>
        <CreateTicketForm onCreate={createTicket} />
        <button className="btn" type="button" onClick={() => void reload()}>
          ↻ Aggiorna
        </button>
      </header>

      {error && <div className="app__error">⚠ {error}</div>}

      <main className="app__main">
        {loading ? (
          <p className="app__loading">Caricamento ticket…</p>
        ) : (
          <TicketBoard tickets={tickets} onChangeStatus={changeStatus} />
        )}
      </main>
    </div>
  );
}
