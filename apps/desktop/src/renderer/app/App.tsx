import { useState } from 'react';
import { useTickets } from '../features/tickets/hooks/useTickets';
import { TicketBoard } from '../features/tickets/components/TicketBoard';
import { CreateTicketForm } from '../features/tickets/components/CreateTicketForm';
import { emailApi } from '../features/email/api/emailApi';
import { EmailAccountsPanel } from '../features/email/components/EmailAccountsPanel';

export function App(): JSX.Element {
  const { tickets, loading, error, reload, createTicket, changeStatus } = useTickets();
  const [accountsOpen, setAccountsOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const syncEmail = async (): Promise<void> => {
    setSyncing(true);
    setNotice(null);
    try {
      const results = await emailApi.sync();
      const created = results.reduce((sum, r) => sum + r.created, 0);
      const errors = results.flatMap((r) => r.errors);
      setNotice(
        errors.length > 0
          ? `Sync con errori: ${errors.join('; ')}`
          : `Sincronizzazione completata: ${created} nuovi ticket.`,
      );
      await reload();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : 'Errore di sincronizzazione');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">Ticket AI Manager</h1>
        <CreateTicketForm onCreate={createTicket} />
        <button className="btn" type="button" onClick={() => void syncEmail()} disabled={syncing}>
          {syncing ? 'Scarico…' : '📥 Scarica email'}
        </button>
        <button className="btn" type="button" onClick={() => setAccountsOpen(true)}>
          ✉ Account email
        </button>
        <button className="btn" type="button" onClick={() => void reload()}>
          ↻ Aggiorna
        </button>
      </header>

      {error && <div className="app__error">⚠ {error}</div>}
      {notice && (
        <div className="app__notice" onClick={() => setNotice(null)}>
          {notice}
        </div>
      )}

      <main className="app__main">
        {loading ? (
          <p className="app__loading">Caricamento ticket…</p>
        ) : (
          <TicketBoard tickets={tickets} onChangeStatus={changeStatus} />
        )}
      </main>

      {accountsOpen && <EmailAccountsPanel onClose={() => setAccountsOpen(false)} />}
    </div>
  );
}
