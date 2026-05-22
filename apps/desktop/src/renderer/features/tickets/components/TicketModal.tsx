import { useEffect, useState } from 'react';
import {
  MessageDirection,
  STATUS_LABELS,
  STATUS_ORDER,
  TYPE_LABELS,
  TicketEventType,
  TicketStatus,
  TicketType,
  type Attachment,
  type CreateTicketInput,
  type Ticket,
  type TicketEvent,
  type TicketMessage,
  type UpdateTicketInput,
} from '@tickethub/shared';
import { useProjects } from '../../projects/hooks/useProjects';
import { ticketsApi } from '../api/ticketsApi';

interface TicketModalProps {
  ticket: Ticket | null; // null = modalità creazione
  onClose: () => void;
  onChangeStatus: (id: number, status: TicketStatus, reviewNote?: string) => Promise<void>;
  onUpdate: (id: number, input: UpdateTicketInput) => Promise<void>;
  onCreate: (input: CreateTicketInput) => Promise<Ticket>;
  getEvents: (id: number) => Promise<TicketEvent[]>;
}

const EVENT_LABELS: Record<TicketEventType, string> = {
  [TicketEventType.Created]: 'Creato',
  [TicketEventType.StatusChange]: 'Stato',
  [TicketEventType.UserNote]: 'Nota utente',
  [TicketEventType.AiNote]: 'AI',
  [TicketEventType.AiDraft]: 'Bozza AI',
  [TicketEventType.Edit]: 'Modifica',
};

const isCode = (t: TicketType): boolean => t === TicketType.Fix || t === TicketType.Feature;

export function TicketModal({
  ticket,
  onClose,
  onChangeStatus,
  onUpdate,
  onCreate,
  getEvents,
}: TicketModalProps): JSX.Element {
  const { projects } = useProjects();
  const [current, setCurrent] = useState<Ticket | null>(ticket);
  const [title, setTitle] = useState(ticket?.title ?? '');
  const [description, setDescription] = useState(ticket?.description ?? '');
  const [type, setType] = useState<TicketType>(ticket?.type ?? TicketType.Email);
  const [projectId, setProjectId] = useState<string>(
    ticket?.project_id ? String(ticket.project_id) : '',
  );
  const [note, setNote] = useState('');
  const [events, setEvents] = useState<TicketEvent[]>([]);
  const [messages, setMessages] = useState<TicketMessage[]>([]);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [busy, setBusy] = useState(false);
  const [status, setStatusMsg] = useState<string | null>(null);

  const isCreate = current === null;

  useEffect(() => {
    if (!current) return;
    void getEvents(current.id).then(setEvents).catch(() => setEvents([]));
    void ticketsApi.messages(current.id).then(setMessages).catch(() => setMessages([]));
    void ticketsApi.attachments(current.id).then(setAttachments).catch(() => setAttachments([]));
  }, [getEvents, current]);

  const refreshAttachments = async (id: number): Promise<void> => {
    setAttachments(await ticketsApi.attachments(id));
  };

  const create = async (): Promise<void> => {
    if (!title.trim()) return;
    setBusy(true);
    try {
      const created = await onCreate({
        title: title.trim(),
        description: description.trim() || null,
        type,
        project_id: isCode(type) && projectId ? Number(projectId) : null,
      });
      setCurrent(created); // passa in modalità modifica (così puoi aggiungere allegati)
      setStatusMsg('Ticket creato ✓ — ora puoi aggiungere allegati.');
    } finally {
      setBusy(false);
    }
  };

  const save = async (): Promise<void> => {
    if (!current) return;
    setBusy(true);
    try {
      await onUpdate(current.id, {
        title: title.trim(),
        description: description.trim() || null,
        type,
        project_id: isCode(type) && projectId ? Number(projectId) : null,
      });
      setStatusMsg('Modifiche salvate ✓');
    } finally {
      setBusy(false);
    }
  };

  const saveNote = async (): Promise<void> => {
    if (!current || !note.trim()) return;
    setBusy(true);
    try {
      await onUpdate(current.id, { review_note: note.trim() });
      setEvents(await getEvents(current.id));
      setStatusMsg('Nota salvata ✓ — l’AI la userà con priorità.');
    } finally {
      setBusy(false);
    }
  };

  const move = async (target: TicketStatus): Promise<void> => {
    if (!current) return;
    setBusy(true);
    try {
      await onChangeStatus(current.id, target, note.trim() || undefined);
      onClose();
    } finally {
      setBusy(false);
    }
  };

  const removeAttachment = async (attId: number): Promise<void> => {
    if (!current) return;
    await ticketsApi.deleteAttachment(current.id, attId);
    await refreshAttachments(current.id);
  };

  const onPickFile = (file: File): void => {
    if (!current) return;
    void ticketsApi.uploadAttachment(current.id, file).then(() => refreshAttachments(current.id));
  };

  return (
    <div
      className="modal"
      role="dialog"
      aria-label={isCreate ? 'Nuovo ticket' : `Ticket #${current?.id}`}
    >
      <div className="modal__backdrop" onClick={onClose} />
      <div className="modal__panel">
        <header className="modal__header">
          <h2>
            {current ? (
              <>
                #{current.id} ·{' '}
                <span className="modal__status">{STATUS_LABELS[current.status]}</span>
              </>
            ) : (
              'Nuovo ticket'
            )}
          </h2>
          <button className="btn btn--sm" type="button" onClick={onClose}>
            ✕
          </button>
        </header>

        <div className="modal__body">
          <div className="modal__main">
            <label className="field">
              <span>Titolo</span>
              <input value={title} onChange={(e) => setTitle(e.target.value)} />
            </label>
            <label className="field">
              <span>Descrizione</span>
              <textarea
                rows={5}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </label>
            <div className="field-row">
              <label className="field">
                <span>Tipo</span>
                <select value={type} onChange={(e) => setType(e.target.value as TicketType)}>
                  {Object.values(TicketType).map((t) => (
                    <option key={t} value={t}>
                      {TYPE_LABELS[t]}
                    </option>
                  ))}
                </select>
              </label>
              {isCode(type) && (
                <label className="field">
                  <span>Progetto</span>
                  <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
                    <option value="">—</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </div>

            {current ? (
              <button
                className="btn btn--primary"
                type="button"
                disabled={busy}
                onClick={() => void save()}
              >
                {busy ? 'Salvo…' : 'Salva modifiche'}
              </button>
            ) : (
              <button
                className="btn btn--primary"
                type="button"
                disabled={busy || !title.trim()}
                onClick={() => void create()}
              >
                {busy ? 'Creo…' : 'Crea ticket'}
              </button>
            )}

            {current && messages.length > 0 && (
              <div className="modal__thread">
                <span className="modal__label">Conversazione</span>
                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={`msg msg--${
                      m.direction === MessageDirection.Inbound ? 'in' : 'out'
                    }`}
                  >
                    <span className="msg__who">
                      {m.direction === MessageDirection.Inbound ? m.from_addr || 'Cliente' : 'Noi'}
                    </span>
                    <p className="msg__body">{m.body}</p>
                  </div>
                ))}
              </div>
            )}

            {current && (
              <div className="modal__attachments">
                <span className="modal__label">Allegati</span>
                <ul className="att-list">
                  {attachments.map((a) => (
                    <li key={a.id} className="att-list__item">
                      <a
                        href={ticketsApi.attachmentUrl(current.id, a.id)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        📎 {a.filename}
                      </a>
                      <span className="att-list__meta">
                        {(a.size / 1024).toFixed(0)} KB
                        <button
                          className="att-list__del"
                          type="button"
                          onClick={() => void removeAttachment(a.id)}
                        >
                          ✕
                        </button>
                      </span>
                    </li>
                  ))}
                  {attachments.length === 0 && <li className="modal__label">Nessun allegato.</li>}
                </ul>
                <label className="att-upload">
                  + Aggiungi allegato
                  <input
                    type="file"
                    hidden
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) onPickFile(file);
                      e.target.value = '';
                    }}
                  />
                </label>
              </div>
            )}

            {current?.ai_draft && (
              <div className="modal__draft">
                <span className="modal__label">Bozza / piano AI</span>
                <pre>{current.ai_draft}</pre>
              </div>
            )}
          </div>

          {current && (
            <aside className="modal__side">
              <span className="modal__label">Sposta a</span>
              <div className="modal__moves">
                {STATUS_ORDER.filter((s) => s !== current.status).map((s) => (
                  <button
                    key={s}
                    className={`btn btn--sm btn--${s}`}
                    type="button"
                    disabled={busy}
                    onClick={() => void move(s)}
                  >
                    {STATUS_LABELS[s]}
                  </button>
                ))}
              </div>
              <label className="field">
                <span>Nota / istruzione per l&apos;AI (priorità massima)</span>
                <textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
              </label>
              <button
                className="btn btn--sm"
                type="button"
                disabled={busy || !note.trim()}
                onClick={() => void saveNote()}
              >
                💾 Salva nota
              </button>
              {status && <p className="modal__label">{status}</p>}

              <span className="modal__label">Cronologia</span>
              <ul className="timeline">
                {events.map((ev) => (
                  <li key={ev.id} className={`timeline__item timeline__item--${ev.type}`}>
                    <div className="timeline__meta">
                      <span className="timeline__type">{EVENT_LABELS[ev.type]}</span>
                      <span className="timeline__time">
                        {new Date(ev.created_at).toLocaleString('it-IT')}
                      </span>
                    </div>
                    <p className="timeline__msg">{ev.message}</p>
                  </li>
                ))}
                {events.length === 0 && <li className="modal__label">Nessun evento.</li>}
              </ul>
            </aside>
          )}
          {isCreate && status && (
            <aside className="modal__side">
              <p className="modal__label">{status}</p>
            </aside>
          )}
        </div>
      </div>
    </div>
  );
}
