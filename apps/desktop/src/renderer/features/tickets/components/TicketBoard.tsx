import { STATUS_LABELS, STATUS_ORDER, TicketStatus, type Ticket } from '@tickethub/shared';
import { TicketCard } from './TicketCard';

interface TicketBoardProps {
  tickets: Ticket[];
  onChangeStatus: (id: number, status: TicketStatus, reviewNote?: string) => void;
}

export function TicketBoard({ tickets, onChangeStatus }: TicketBoardProps): JSX.Element {
  return (
    <div className="board">
      {STATUS_ORDER.map((status) => {
        const items = tickets.filter((t) => t.status === status);
        return (
          <section key={status} className="board__column">
            <header className="board__column-header">
              <span>{STATUS_LABELS[status]}</span>
              <span className="board__count">{items.length}</span>
            </header>
            <div className="board__column-body">
              {items.map((ticket) => (
                <TicketCard key={ticket.id} ticket={ticket} onChangeStatus={onChangeStatus} />
              ))}
              {items.length === 0 && <p className="board__empty">Nessun ticket</p>}
            </div>
          </section>
        );
      })}
    </div>
  );
}
