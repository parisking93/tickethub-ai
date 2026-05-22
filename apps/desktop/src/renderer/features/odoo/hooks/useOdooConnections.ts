import { useCallback, useEffect, useState } from 'react';
import type { CreateOdooConnectionInput, OdooConnection, OdooSyncResult } from '@tickethub/shared';
import { odooApi } from '../api/odooApi';

interface UseOdooResult {
  connections: OdooConnection[];
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  addConnection: (input: CreateOdooConnectionInput) => Promise<void>;
  removeConnection: (id: number) => Promise<void>;
  sync: () => Promise<OdooSyncResult[]>;
}

export function useOdooConnections(): UseOdooResult {
  const [connections, setConnections] = useState<OdooConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setConnections(await odooApi.listConnections());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore caricamento connessioni');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const addConnection = useCallback(
    async (input: CreateOdooConnectionInput) => {
      await odooApi.createConnection(input);
      await reload();
    },
    [reload],
  );

  const removeConnection = useCallback(
    async (id: number) => {
      await odooApi.deleteConnection(id);
      await reload();
    },
    [reload],
  );

  const sync = useCallback(async () => odooApi.sync(), []);

  return { connections, loading, error, reload, addConnection, removeConnection, sync };
}
