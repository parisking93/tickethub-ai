import { useState } from 'react';
import type { Ticket } from '@tickethub/shared';
import { useTickets } from '../features/tickets/hooks/useTickets';
import { TicketBoard } from '../features/tickets/components/TicketBoard';
import { TicketModal } from '../features/tickets/components/TicketModal';
import { emailApi } from '../features/email/api/emailApi';
import { EmailAccountsPanel } from '../features/email/components/EmailAccountsPanel';
import { ProjectsPanel } from '../features/projects/components/ProjectsPanel';
import { OdooPanel } from '../features/odoo/components/OdooPanel';
import { AIProfilesPanel } from '../features/ai/components/AIProfilesPanel';

export function App(): JSX.Element {
  const { tickets, loading, error, reload, createTicket, changeStatus, updateTicket, getEvents } =
    useTickets();
  // modalState: undefined = chiuso, null = creazione, Ticket = dettaglio
  const [modalState, setModalState] = useState<Ticket | null | undefined>(undefined);
  const [accountsOpen, setAccountsOpen] = useState(false);
  const [projectsOpen, setProjectsOpen] = useState(false);
  const [odooOpen, setOdooOpen] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const modalOpen = modalState !== undefined;

  const closeModal = (): void => {
    setModalState(undefined);
    void reload();
  };

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
        <button className="btn btn--primary" type="button" onClick={() => setModalState(null)}>
          ➕ Crea ticket
        </button>
        <button className="btn" type="button" onClick={() => void syncEmail()} disabled={syncing}>
          {syncing ? 'Scarico…' : '📥 Scarica email'}
        </button>
        <button className="btn" type="button" onClick={() => setAccountsOpen(true)}>
          ✉ Account email
        </button>
        <button className="btn" type="button" onClick={() => setProjectsOpen(true)}>
          🗂 Progetti
        </button>
        <button className="btn" type="button" onClick={() => setOdooOpen(true)}>
          🔗 Odoo
        </button>
        <button className="btn" type="button" onClick={() => setAiOpen(true)}>
          ⚙ Area personale
        </button>
        <button className="btn" type="button" onClick={() => void reload()}>
          ↻ Aggiorna
        </button>
      </header>

      <div className="app__subbar">
        <span className="app__badge">🤖 Job AI automatico attivo (ogni minuto)</span>
        {error && <span className="app__error-inline">⚠ {error}</span>}
      </div>

      {notice && (
        <div className="app__notice" onClick={() => setNotice(null)}>
          {notice}
        </div>
      )}

      <main className="app__main">
        {loading ? (
          <p className="app__loading">Caricamento ticket…</p>
        ) : (
          <TicketBoard tickets={tickets} onOpen={setModalState} onMove={changeStatus} />
        )}
      </main>

      {modalOpen && (
        <TicketModal
          ticket={modalState ?? null}
          onClose={closeModal}
          onChangeStatus={changeStatus}
          onUpdate={updateTicket}
          onCreate={createTicket}
          getEvents={getEvents}
        />
      )}
      {accountsOpen && <EmailAccountsPanel onClose={() => setAccountsOpen(false)} />}
      {projectsOpen && <ProjectsPanel onClose={() => setProjectsOpen(false)} />}
      {odooOpen && <OdooPanel onClose={() => setOdooOpen(false)} onSynced={() => void reload()} />}
      {aiOpen && <AIProfilesPanel onClose={() => setAiOpen(false)} />}
    </div>
  );
}
