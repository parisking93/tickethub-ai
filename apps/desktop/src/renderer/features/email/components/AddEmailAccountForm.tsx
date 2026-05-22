import { useState } from 'react';
import {
  DEFAULT_AUTH,
  EmailAuthType,
  EmailProvider,
  PROVIDER_LABELS,
  type CreateEmailAccountInput,
} from '@tickethub/shared';

interface AddEmailAccountFormProps {
  onAdd: (input: CreateEmailAccountInput) => Promise<void>;
}

export function AddEmailAccountForm({ onAdd }: AddEmailAccountFormProps): JSX.Element {
  const [email, setEmail] = useState('');
  const [provider, setProvider] = useState<EmailProvider>(EmailProvider.Gmail);
  const [authType, setAuthType] = useState<EmailAuthType>(EmailAuthType.Password);
  const [secret, setSecret] = useState('');
  const [clientId, setClientId] = useState('');
  const [imapHost, setImapHost] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onProviderChange = (next: EmailProvider): void => {
    setProvider(next);
    setAuthType(DEFAULT_AUTH[next]);
  };

  const submit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onAdd({
        email: email.trim(),
        provider,
        auth_type: authType,
        secret: authType === EmailAuthType.Password ? secret : null,
        oauth_client_id: authType === EmailAuthType.OAuth2 ? clientId || null : null,
        imap_host: provider === EmailProvider.Imap ? imapHost.trim() : null,
      });
      setEmail('');
      setSecret('');
      setClientId('');
      setImapHost('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore creazione account');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="email-form" onSubmit={submit}>
      <div className="email-form__row">
        <input
          className="email-form__field"
          type="email"
          placeholder="indirizzo email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <select
          className="email-form__field"
          value={provider}
          onChange={(e) => onProviderChange(e.target.value as EmailProvider)}
        >
          {Object.values(EmailProvider).map((p) => (
            <option key={p} value={p}>
              {PROVIDER_LABELS[p]}
            </option>
          ))}
        </select>
        <select
          className="email-form__field"
          value={authType}
          onChange={(e) => setAuthType(e.target.value as EmailAuthType)}
        >
          <option value={EmailAuthType.Password}>Password dedicata</option>
          <option value={EmailAuthType.OAuth2}>OAuth2</option>
        </select>
      </div>

      <div className="email-form__row">
        {provider === EmailProvider.Imap && (
          <input
            className="email-form__field"
            type="text"
            placeholder="host IMAP (es. mail.dominio.it)"
            value={imapHost}
            onChange={(e) => setImapHost(e.target.value)}
            required
          />
        )}
        {authType === EmailAuthType.Password ? (
          <input
            className="email-form__field"
            type="password"
            placeholder="password dedicata / app password"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
            required
          />
        ) : (
          <input
            className="email-form__field"
            type="text"
            placeholder="OAuth client_id (Azure) — opzionale se in .env"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
          />
        )}
        <button className="btn btn--primary" type="submit" disabled={submitting}>
          {submitting ? 'Aggiungo…' : 'Aggiungi account'}
        </button>
      </div>

      {error && <p className="email-form__error">⚠ {error}</p>}
    </form>
  );
}
