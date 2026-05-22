import { useEffect, useState } from 'react';
import type { AIProfile, AIProvider, UpdateAIProfileInput } from '@tickethub/shared';
import { aiApi } from '../api/aiApi';

interface AIProfilesPanelProps {
  onClose: () => void;
}

const PROVIDERS: { value: AIProvider; label: string }[] = [
  { value: 'ollama', label: 'Ollama (locale)' },
  { value: 'lmstudio', label: 'LM Studio (locale)' },
  { value: 'openai_compatible', label: 'Remoto (OpenAI-compatible)' },
];

type ModelKey = 'model_email' | 'model_fix' | 'model_feature' | 'model_vision';

const OPERATIONS: { key: ModelKey; label: string }[] = [
  { key: 'model_email', label: 'Email (bozze/risposte)' },
  { key: 'model_fix', label: 'Ticket Fix' },
  { key: 'model_feature', label: 'Ticket Feature (CR)' },
  { key: 'model_vision', label: 'Immagini (vision)' },
];

const NEW = -1;

export function AIProfilesPanel({ onClose }: AIProfilesPanelProps): JSX.Element {
  const [profiles, setProfiles] = useState<AIProfile[]>([]);
  const [selectedId, setSelectedId] = useState<number>(NEW);
  const [name, setName] = useState('');
  const [provider, setProvider] = useState<AIProvider>('ollama');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [models, setModels] = useState<Record<ModelKey, string>>({
    model_email: '',
    model_fix: '',
    model_feature: '',
    model_vision: '',
  });
  const [available, setAvailable] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<string | null>(null);

  const isNew = selectedId === NEW;

  useEffect(() => {
    void (async () => {
      try {
        const list = await aiApi.listProfiles();
        setProfiles(list);
        const active = list.find((p) => p.is_active) ?? list[0];
        if (active) loadProfile(active);
      } catch {
        setStatus('Impossibile caricare i profili.');
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function loadProfile(p: AIProfile): void {
    setSelectedId(p.id);
    setName(p.name);
    setProvider(p.provider);
    setBaseUrl(p.base_url ?? '');
    setApiKey('');
    setModels({
      model_email: p.model_email,
      model_fix: p.model_fix,
      model_feature: p.model_feature,
      model_vision: p.model_vision,
    });
    void refreshModels(p.provider, p.base_url ?? '', false);
  }

  function startNew(): void {
    setSelectedId(NEW);
    setName('');
    setProvider('ollama');
    setBaseUrl('');
    setApiKey('');
    setModels({ model_email: '', model_fix: '', model_feature: '', model_vision: '' });
    void refreshModels('ollama', '', true);
  }

  async function refreshModels(prov: string, url: string, adjust: boolean): Promise<void> {
    setStatus('Carico i modelli…');
    try {
      const list = await aiApi.models(prov, url || undefined);
      setAvailable(list.models);
      if (adjust && list.models.length > 0) {
        // picklist dinamica: imposta i modelli mancanti al primo disponibile
        setModels((prev) => {
          const next = { ...prev };
          (Object.keys(next) as ModelKey[]).forEach((k) => {
            if (!list.models.includes(next[k])) next[k] = list.models[0];
          });
          return next;
        });
      }
      setStatus(list.models.length ? null : 'Nessun modello (provider raggiungibile?).');
    } catch (err) {
      setAvailable([]);
      setStatus(err instanceof Error ? err.message : 'Provider non raggiungibile.');
    }
  }

  const onProviderChange = (p: AIProvider): void => {
    setProvider(p);
    void refreshModels(p, baseUrl, true); // cambia tutto in automatico
  };

  const onSelectProfile = (value: string): void => {
    if (value === 'new') {
      startNew();
      return;
    }
    const p = profiles.find((x) => x.id === Number(value));
    if (p) loadProfile(p);
  };

  const save = async (): Promise<void> => {
    if (!name.trim()) {
      setStatus('Dai un nome al profilo.');
      return;
    }
    setStatus('Salvo…');
    try {
      const payload: UpdateAIProfileInput = {
        name: name.trim(),
        provider,
        base_url: baseUrl.trim() || null,
        ...(apiKey.trim() ? { api_key: apiKey.trim() } : {}),
        ...models,
      };
      const saved = isNew
        ? await aiApi.createProfile({ name: name.trim(), ...payload })
        : await aiApi.updateProfile(selectedId, payload);
      const list = await aiApi.listProfiles();
      setProfiles(list);
      setSelectedId(saved.id);
      setStatus('Profilo salvato ✓');
    } catch (err) {
      setStatus(err instanceof Error ? err.message : 'Errore salvataggio.');
    }
  };

  const activate = async (): Promise<void> => {
    if (isNew) return;
    await aiApi.activateProfile(selectedId);
    setProfiles(await aiApi.listProfiles());
    setStatus('Profilo attivato ✓ — il job userà questo.');
  };

  const remove = async (): Promise<void> => {
    if (isNew) return;
    await aiApi.deleteProfile(selectedId);
    const list = await aiApi.listProfiles();
    setProfiles(list);
    if (list[0]) loadProfile(list[0]);
    else startNew();
  };

  const options = (current: string): string[] =>
    available.includes(current) || !current ? available : [current, ...available];

  const activeProfile = profiles.find((p) => p.is_active);

  return (
    <div className="drawer" role="dialog" aria-label="Profili AI">
      <div className="drawer__backdrop" onClick={onClose} />
      <aside className="drawer__panel">
        <header className="drawer__header">
          <h2>Area personale · Profili AI</h2>
          <button className="btn btn--sm" type="button" onClick={onClose}>
            ✕
          </button>
        </header>

        {loading ? (
          <p className="drawer__muted">Caricamento…</p>
        ) : (
          <>
            <label className="field">
              <span>Profilo {activeProfile ? `(attivo: ${activeProfile.name})` : ''}</span>
              <select value={isNew ? 'new' : String(selectedId)} onChange={(e) => onSelectProfile(e.target.value)}>
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.is_active ? '★ ' : ''}
                    {p.name}
                  </option>
                ))}
                <option value="new">+ Nuovo profilo…</option>
              </select>
            </label>

            <label className="field">
              <span>Nome profilo</span>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="es. Locale Ollama" />
            </label>

            <label className="field">
              <span>Provider</span>
              <select value={provider} onChange={(e) => onProviderChange(e.target.value as AIProvider)}>
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
                onBlur={() => void refreshModels(provider, baseUrl, true)}
                placeholder="es. http://localhost:1234/v1"
              />
            </label>

            {provider === 'openai_compatible' && (
              <label className="field">
                <span>API key (vuoto = non modificare)</span>
                <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
              </label>
            )}

            <span className="modal__label">Modello per operazione</span>
            {OPERATIONS.map((op) => (
              <label key={op.key} className="field">
                <span>{op.label}</span>
                <select
                  value={models[op.key]}
                  onChange={(e) => setModels({ ...models, [op.key]: e.target.value })}
                >
                  {options(models[op.key]).map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </label>
            ))}

            <div className="email-form__row">
              <button className="btn btn--primary" type="button" onClick={() => void save()}>
                {isNew ? 'Crea profilo' : 'Salva profilo'}
              </button>
              {!isNew && (
                <button className="btn" type="button" onClick={() => void activate()}>
                  ★ Attiva
                </button>
              )}
              {!isNew && profiles.length > 1 && (
                <button className="btn btn--rifiutato" type="button" onClick={() => void remove()}>
                  Elimina
                </button>
              )}
            </div>
            {status && <p className="drawer__muted">{status}</p>}
          </>
        )}
      </aside>
    </div>
  );
}
