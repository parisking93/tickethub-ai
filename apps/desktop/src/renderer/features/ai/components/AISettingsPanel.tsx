import { useEffect, useState } from 'react';
import type { AIProvider, UpdateAISettingsInput } from '@tickethub/shared';
import { aiApi } from '../api/aiApi';

interface AISettingsPanelProps {
  onClose: () => void;
}

const PROVIDERS: { value: AIProvider; label: string }[] = [
  { value: 'ollama', label: 'Ollama (locale)' },
  { value: 'lmstudio', label: 'LM Studio (locale)' },
  { value: 'openai_compatible', label: 'Remoto (OpenAI-compatible)' },
];

const OPERATIONS: { key: keyof UpdateAISettingsInput; label: string }[] = [
  { key: 'model_email', label: 'Email (bozze/risposte)' },
  { key: 'model_fix', label: 'Ticket Fix' },
  { key: 'model_feature', label: 'Ticket Feature (CR)' },
  { key: 'model_vision', label: 'Immagini (vision)' },
];

export function AISettingsPanel({ onClose }: AISettingsPanelProps): JSX.Element {
  const [provider, setProvider] = useState<AIProvider>('ollama');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [models, setModels] = useState<Record<string, string>>({});
  const [available, setAvailable] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const s = await aiApi.getSettings();
        setProvider(s.provider);
        setBaseUrl(s.base_url ?? '');
        setModels({
          model_email: s.model_email,
          model_fix: s.model_fix,
          model_feature: s.model_feature,
          model_vision: s.model_vision,
        });
      } catch {
        setStatus('Impossibile caricare la configurazione.');
      } finally {
        setLoading(false);
      }
      await refreshModels('ollama', '');
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshModels = async (prov: string, url: string): Promise<void> => {
    setStatus('Carico i modelli…');
    try {
      const list = await aiApi.models(prov, url || undefined);
      setAvailable(list.models);
      setStatus(list.models.length ? null : 'Nessun modello trovato (provider raggiungibile?).');
    } catch (err) {
      setAvailable([]);
      setStatus(err instanceof Error ? err.message : 'Provider non raggiungibile.');
    }
  };

  const save = async (): Promise<void> => {
    setStatus('Salvo…');
    try {
      const input: UpdateAISettingsInput = {
        provider,
        base_url: baseUrl.trim() || null,
        ...(apiKey.trim() ? { api_key: apiKey.trim() } : {}),
        model_email: models.model_email,
        model_fix: models.model_fix,
        model_feature: models.model_feature,
        model_vision: models.model_vision,
      };
      await aiApi.updateSettings(input);
      setStatus('Configurazione salvata ✓');
    } catch (err) {
      setStatus(err instanceof Error ? err.message : 'Errore salvataggio.');
    }
  };

  const options = (current: string): string[] =>
    available.includes(current) || !current ? available : [current, ...available];

  return (
    <div className="drawer" role="dialog" aria-label="Area personale AI">
      <div className="drawer__backdrop" onClick={onClose} />
      <aside className="drawer__panel">
        <header className="drawer__header">
          <h2>Area personale · AI</h2>
          <button className="btn btn--sm" type="button" onClick={onClose}>
            ✕
          </button>
        </header>

        {loading ? (
          <p className="drawer__muted">Caricamento…</p>
        ) : (
          <>
            <label className="field">
              <span>Provider</span>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value as AIProvider)}
              >
                {PROVIDERS.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Base URL (vuoto = default del provider)</span>
              <input
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="es. http://localhost:11434"
              />
            </label>

            {provider === 'openai_compatible' && (
              <label className="field">
                <span>API key (lascia vuoto per non modificare)</span>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
              </label>
            )}

            <button
              className="btn btn--sm"
              type="button"
              onClick={() => void refreshModels(provider, baseUrl)}
            >
              ↻ Aggiorna elenco modelli
            </button>

            <span className="modal__label" style={{ marginTop: 8 }}>
              Modello per operazione
            </span>
            {OPERATIONS.map((op) => (
              <label key={op.key} className="field">
                <span>{op.label}</span>
                <select
                  value={(models[op.key] as string) ?? ''}
                  onChange={(e) => setModels({ ...models, [op.key]: e.target.value })}
                >
                  {options((models[op.key] as string) ?? '').map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </label>
            ))}

            <button className="btn btn--primary" type="button" onClick={() => void save()}>
              Salva configurazione
            </button>
            {status && <p className="drawer__muted">{status}</p>}
          </>
        )}
      </aside>
    </div>
  );
}
