import { useState } from 'react';
import { TYPE_LABELS, TicketType, type CreateOdooConnectionInput } from '@tickethub/shared';

interface AddOdooConnectionFormProps {
  onAdd: (input: CreateOdooConnectionInput) => Promise<void>;
}

export function AddOdooConnectionForm({ onAdd }: AddOdooConnectionFormProps): JSX.Element {
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [dbName, setDbName] = useState('');
  const [username, setUsername] = useState('');
  const [secret, setSecret] = useState('');
  const [ticketModel, setTicketModel] = useState('helpdesk.ticket');
  const [defaultType, setDefaultType] = useState<TicketType>(TicketType.Fix);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onAdd({
        name: name.trim(),
        url: url.trim(),
        db_name: dbName.trim(),
        username: username.trim(),
        secret,
        ticket_model: ticketModel.trim() || 'helpdesk.ticket',
        default_type: defaultType,
      });
      setName('');
      setUrl('');
      setDbName('');
      setUsername('');
      setSecret('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore creazione connessione');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="email-form" onSubmit={submit}>
      <div className="email-form__row">
        <input
          className="email-form__field"
          placeholder="nome"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          className="email-form__field"
          placeholder="URL Odoo (https://…)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
        />
      </div>
      <div className="email-form__row">
        <input
          className="email-form__field"
          placeholder="database"
          value={dbName}
          onChange={(e) => setDbName(e.target.value)}
          required
        />
        <input
          className="email-form__field"
          placeholder="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
      </div>
      <div className="email-form__row">
        <input
          className="email-form__field"
          type="password"
          placeholder="password / API key"
          value={secret}
          onChange={(e) => setSecret(e.target.value)}
          required
        />
        <input
          className="email-form__field"
          placeholder="modello (helpdesk.ticket)"
          value={ticketModel}
          onChange={(e) => setTicketModel(e.target.value)}
        />
      </div>
      <div className="email-form__row">
        <select
          className="email-form__field"
          value={defaultType}
          onChange={(e) => setDefaultType(e.target.value as TicketType)}
        >
          {Object.values(TicketType).map((t) => (
            <option key={t} value={t}>
              {TYPE_LABELS[t]}
            </option>
          ))}
        </select>
        <button className="btn btn--primary" type="submit" disabled={submitting}>
          {submitting ? 'Aggiungo…' : 'Aggiungi connessione'}
        </button>
      </div>
      {error && <p className="email-form__error">⚠ {error}</p>}
    </form>
  );
}
