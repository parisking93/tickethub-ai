import { TYPE_LABELS, type Ticket } from '@tickethub/shared';

interface TicketCardProps {
  ticket: Ticket;
  onOpen: (ticket: Ticket) => void;
  onDragStart: (ticket: Ticket) => void;
  onDragEnd: () => void;
}

export function TicketCard({ ticket, onOpen, onDragStart, onDragEnd }: TicketCardProps): JSX.Element {
  return (
    <article
      className={`ticket-card ticket-card--${ticket.type}`}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/ticket-id', String(ticket.id));
        onDragStart(ticket);
      }}
      onDragEnd={onDragEnd}
      onClick={() => onOpen(ticket)}
    >
      <header className="ticket-card__header">
        <span className="ticket-card__id">#{ticket.id}</span>
        <span className={`ticket-card__type ticket-card__type--${ticket.type}`}>
          {TYPE_LABELS[ticket.type]}
        </span>
      </header>

      <h3 className="ticket-card__title">{ticket.title}</h3>

      {ticket.ai_note && <p className="ticket-card__ai-note">{ticket.ai_note}</p>}
      {ticket.branch_name && <code className="ticket-card__branch">{ticket.branch_name}</code>}
    </article>
  );
}
