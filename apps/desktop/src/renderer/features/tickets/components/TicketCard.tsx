import { useState } from 'react';
import { STATUS_LABELS, TYPE_LABELS, TicketStatus, type Ticket } from '@tickethub/shared';
import { ALLOWED_TRANSITIONS } from '../transitions';

interface TicketCardProps {
  ticket: Ticket;
  onChangeStatus: (id: number, status: TicketStatus, reviewNote?: string) => void;
}

export function TicketCard({ ticket, onChangeStatus }: TicketCardProps): JSX.Element {
  const [reviewNote, setReviewNote] = useState('');
  const nextStates = ALLOWED_TRANSITIONS[ticket.status];

  const handle = (status: TicketStatus): void => {
    const needsNote = status === TicketStatus.Rifiutato;
    onChangeStatus(ticket.id, status, needsNote ? reviewNote || undefined : undefined);
    setReviewNote('');
  };

  return (
    <article className={`ticket-card ticket-card--${ticket.type}`}>
      <header className="ticket-card__header">
        <span className="ticket-card__id">#{ticket.id}</span>
        <span className={`ticket-card__type ticket-card__type--${ticket.type}`}>
          {TYPE_LABELS[ticket.type]}
        </span>
      </header>

      <h3 className="ticket-card__title">{ticket.title}</h3>
      {ticket.description && <p className="ticket-card__desc">{ticket.description}</p>}

      {ticket.ai_note && (
        <p className="ticket-card__ai-note">
          <strong>AI:</strong> {ticket.ai_note}
        </p>
      )}
      {ticket.review_note && (
        <p className="ticket-card__review-note">
          <strong>Note:</strong> {ticket.review_note}
        </p>
      )}
      {ticket.branch_name && <code className="ticket-card__branch">{ticket.branch_name}</code>}

      {ticket.status === TicketStatus.InAttesa && (
        <input
          className="ticket-card__note-input"
          type="text"
          placeholder="Nota (per rifiuto)…"
          value={reviewNote}
          onChange={(e) => setReviewNote(e.target.value)}
        />
      )}

      {nextStates.length > 0 && (
        <footer className="ticket-card__actions">
          {nextStates.map((status) => (
            <button
              key={status}
              type="button"
              className={`btn btn--sm btn--${status}`}
              onClick={() => handle(status)}
            >
              {STATUS_LABELS[status]}
            </button>
          ))}
        </footer>
      )}
    </article>
  );
}
