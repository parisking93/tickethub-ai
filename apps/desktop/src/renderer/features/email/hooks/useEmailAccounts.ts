import { useCallback, useEffect, useState } from 'react';
import type { CreateEmailAccountInput, EmailAccount, EmailSyncResult } from '@tickethub/shared';
import { emailApi } from '../api/emailApi';

interface UseEmailAccountsResult {
  accounts: EmailAccount[];
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  addAccount: (input: CreateEmailAccountInput) => Promise<void>;
  removeAccount: (id: number) => Promise<void>;
  connectOAuth: (id: number) => Promise<void>;
  syncAll: () => Promise<EmailSyncResult[]>;
}

export function useEmailAccounts(): UseEmailAccountsResult {
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setAccounts(await emailApi.listAccounts());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore di caricamento account');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const addAccount = useCallback(
    async (input: CreateEmailAccountInput) => {
      await emailApi.createAccount(input);
      await reload();
    },
    [reload],
  );

  const removeAccount = useCallback(
    async (id: number) => {
      await emailApi.deleteAccount(id);
      await reload();
    },
    [reload],
  );

  const connectOAuth = useCallback(
    async (id: number) => {
      const { authorize_url } = await emailApi.startOAuth(id);
      // Apre il login Microsoft nel browser di sistema (gestito dal main process).
      window.open(authorize_url, '_blank');
    },
    [],
  );

  const syncAll = useCallback(async () => emailApi.sync(), []);

  return { accounts, loading, error, reload, addAccount, removeAccount, connectOAuth, syncAll };
}
