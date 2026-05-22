import { EmailAuthType, PROVIDER_LABELS, type EmailAccount } from '@tickethub/shared';
import { useEmailAccounts } from '../hooks/useEmailAccounts';
import { AddEmailAccountForm } from './AddEmailAccountForm';

interface EmailAccountsPanelProps {
  onClose: () => void;
}

export function EmailAccountsPanel({ onClose }: EmailAccountsPanelProps): JSX.Element {
  const { accounts, loading, error, addAccount, removeAccount, connectOAuth } = useEmailAccounts();

  return (
    <div className="drawer" role="dialog" aria-label="Account email">
      <div className="drawer__backdrop" onClick={onClose} />
      <aside className="drawer__panel">
        <header className="drawer__header">
          <h2>Account email</h2>
          <button className="btn btn--sm" type="button" onClick={onClose}>
            ✕
          </button>
        </header>

        <AddEmailAccountForm onAdd={addAccount} />

        {error && <p className="drawer__error">⚠ {error}</p>}
        {loading ? (
          <p className="drawer__muted">Caricamento…</p>
        ) : accounts.length === 0 ? (
          <p className="drawer__muted">Nessun account configurato.</p>
        ) : (
          <ul className="account-list">
            {accounts.map((acc) => (
              <AccountRow
                key={acc.id}
                account={acc}
                onConnect={() => void connectOAuth(acc.id)}
                onRemove={() => void removeAccount(acc.id)}
              />
            ))}
          </ul>
        )}
      </aside>
    </div>
  );
}

interface AccountRowProps {
  account: EmailAccount;
  onConnect: () => void;
  onRemove: () => void;
}

function AccountRow({ account, onConnect, onRemove }: AccountRowProps): JSX.Element {
  const needsOAuth = account.auth_type === EmailAuthType.OAuth2 && !account.is_authorized;

  return (
    <li className="account-list__item">
      <div className="account-list__info">
        <span className="account-list__email">{account.email}</span>
        <span className="account-list__meta">
          {PROVIDER_LABELS[account.provider]} · {account.auth_type}
        </span>
      </div>
      <div className="account-list__status">
        {account.is_authorized ? (
          <span className="badge badge--ok">autorizzato</span>
        ) : (
          <span className="badge badge--warn">da autorizzare</span>
        )}
      </div>
      <div className="account-list__actions">
        {needsOAuth && (
          <button className="btn btn--sm btn--primary" type="button" onClick={onConnect}>
            Connetti
          </button>
        )}
        <button className="btn btn--sm btn--rifiutato" type="button" onClick={onRemove}>
          Elimina
        </button>
      </div>
    </li>
  );
}
