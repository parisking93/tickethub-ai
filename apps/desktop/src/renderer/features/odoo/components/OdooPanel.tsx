import { useState } from 'react';
import type { OdooConnection } from '@tickethub/shared';
import { useOdooConnections } from '../hooks/useOdooConnections';
import { AddOdooConnectionForm } from './AddOdooConnectionForm';

interface OdooPanelProps {
  onClose: () => void;
  onSynced?: () => void;
}

export function OdooPanel({ onClose, onSynced }: OdooPanelProps): JSX.Element {
  const { connections, loading, error, addConnection, removeConnection, sync } =
    useOdooConnections();
  const [syncing, setSyncing] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const runSync = async (): Promise<void> => {
    setSyncing(true);
    setNotice(null);
    try {
      const results = await sync();
      const created = results.reduce((s, r) => s + r.created, 0);
      const errs = results.flatMap((r) => r.errors);
      setNotice(errs.length > 0 ? `Sync con errori: ${errs.join('; ')}` : `Importati: ${created}`);
      onSynced?.();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : 'Errore sync');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="drawer" role="dialog" aria-label="Connessioni Odoo">
      <div className="drawer__backdrop" onClick={onClose} />
      <aside className="drawer__panel">
        <header className="drawer__header">
          <h2>Connessioni Odoo</h2>
          <div className="account-list__actions">
            <button className="btn btn--sm" type="button" onClick={() => void runSync()} disabled={syncing}>
              {syncing ? 'Importo…' : '↧ Importa ticket'}
            </button>
            <button className="btn btn--sm" type="button" onClick={onClose}>
              ✕
            </button>
          </div>
        </header>

        <AddOdooConnectionForm onAdd={addConnection} />

        {notice && <p className="drawer__muted">{notice}</p>}
        {error && <p className="drawer__error">⚠ {error}</p>}
        {loading ? (
          <p className="drawer__muted">Caricamento…</p>
        ) : connections.length === 0 ? (
          <p className="drawer__muted">Nessuna connessione configurata.</p>
        ) : (
          <ul className="account-list">
            {connections.map((c) => (
              <ConnectionRow key={c.id} conn={c} onRemove={() => void removeConnection(c.id)} />
            ))}
          </ul>
        )}
      </aside>
    </div>
  );
}

function ConnectionRow({
  conn,
  onRemove,
}: {
  conn: OdooConnection;
  onRemove: () => void;
}): JSX.Element {
  return (
    <li className="account-list__item">
      <div className="account-list__info">
        <span className="account-list__email">{conn.name}</span>
        <span className="account-list__meta">
          {conn.url} · {conn.db_name} · {conn.ticket_model} → {conn.default_type}
        </span>
      </div>
      <div className="account-list__actions">
        <button className="btn btn--sm btn--rifiutato" type="button" onClick={onRemove}>
          Elimina
        </button>
      </div>
    </li>
  );
}
