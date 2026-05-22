import { useEffect, useState } from 'react';
import {
  STATUS_LABELS,
  STATUS_ORDER,
  TYPE_LABELS,
  TicketEventType,
  TicketStatus,
  TicketType,
  type Ticket,
  type TicketEvent,
  type UpdateTicketInput,
} from '@tickethub/shared';
import { useProjects } from '../../projects/hooks/useProjects';

interface TicketModalProps {
  ticket: Ticket;
  onClose: () => void;
  onChangeStatus: (id: number, status: TicketStatus, reviewNote?: string) => Promise<void>;
  onUpdate: (id: number, input: UpdateTicketInput) => Promise<void>;
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
  getEvents,
}: TicketModalProps): JSX.Element {
  const { projects } = useProjects();
  const [title, setTitle] = useState(ticket.title);
  const [description, setDescription] = useState(ticket.description ?? '');
  const [type, setType] = useState<TicketType>(ticket.type);
  const [projectId, setProjectId] = useState<string>(ticket.project_id ? String(ticket.project_id) : '');
  const [note, setNote] = useState('');
  const [events, setEvents] = useState<TicketEvent[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void getEvents(ticket.id).then(setEvents).catch(() => setEvents([]));
  }, [getEvents, ticket.id]);

  const dirty =
    title !== ticket.title ||
    description !== (ticket.description ?? '') ||
    type !== ticket.type ||
    projectId !== (ticket.project_id ? String(ticket.project_id) : '');

  const save = async (): Promise<void> => {
    setBusy(true);
    try {
      await onUpdate(ticket.id, {
        title: title.trim(),
        description: description.trim() || null,
        type,
        project_id: isCode(type) && projectId ? Number(projectId) : null,
      });
      onClose();
    } finally {
      setBusy(false);
    }
  };

  const move = async (status: TicketStatus): Promise<void> => {
    setBusy(true);
    try {
      await onChangeStatus(ticket.id, status, note.trim() || undefined);
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal" role="dialog" aria-label={`Ticket #${ticket.id}`}>
      <div className="modal__backdrop" onClick={onClose} />
      <div className="modal__panel">
        <header className="modal__header">
          <h2>
            #{ticket.id} · <span className="modal__status">{STATUS_LABELS[ticket.status]}</span>
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

            <button className="btn btn--primary" type="button" disabled={!dirty || busy} onClick={() => void save()}>
              {busy ? 'Salvo…' : 'Salva modifiche'}
            </button>

            {ticket.ai_draft && (
              <div className="modal__draft">
                <span className="modal__label">Bozza / piano AI</span>
                <pre>{ticket.ai_draft}</pre>
              </div>
            )}
          </div>

          <aside className="modal__side">
            <span className="modal__label">Sposta a</span>
            <div className="modal__moves">
              {STATUS_ORDER.filter((s) => s !== ticket.status).map((s) => (
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
              <span>Nota (per rimandare in lavorazione / rifiutare)</span>
              <textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
            </label>

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
        </div>
      </div>
    </div>
  );
}
