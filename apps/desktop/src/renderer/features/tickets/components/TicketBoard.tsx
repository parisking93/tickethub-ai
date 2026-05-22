import { useState } from 'react';
import { STATUS_LABELS, STATUS_ORDER, TicketStatus, type Ticket } from '@tickethub/shared';
import { TicketCard } from './TicketCard';

interface TicketBoardProps {
  tickets: Ticket[];
  onOpen: (ticket: Ticket) => void;
  onMove: (id: number, status: TicketStatus) => void;
}

export function TicketBoard({ tickets, onOpen, onMove }: TicketBoardProps): JSX.Element {
  const [dragId, setDragId] = useState<number | null>(null);
  const [overStatus, setOverStatus] = useState<TicketStatus | null>(null);

  const handleDrop = (status: TicketStatus): void => {
    setOverStatus(null);
    if (dragId == null) return;
    const ticket = tickets.find((t) => t.id === dragId);
    setDragId(null);
    if (ticket && ticket.status !== status) onMove(ticket.id, status);
  };

  return (
    <div className="board">
      {STATUS_ORDER.map((status) => {
        const items = tickets.filter((t) => t.status === status);
        const isOver = overStatus === status;
        return (
          <section
            key={status}
            className={`board__column${isOver ? ' board__column--over' : ''}`}
            onDragOver={(e) => {
              e.preventDefault();
              if (overStatus !== status) setOverStatus(status);
            }}
            onDragLeave={() => setOverStatus((s) => (s === status ? null : s))}
            onDrop={() => handleDrop(status)}
          >
            <header className="board__column-header">
              <span>{STATUS_LABELS[status]}</span>
              <span className="board__count">{items.length}</span>
            </header>
            <div className="board__column-body">
              {items.map((ticket) => (
                <TicketCard
                  key={ticket.id}
                  ticket={ticket}
                  onOpen={onOpen}
                  onDragStart={(t) => setDragId(t.id)}
                  onDragEnd={() => {
                    setDragId(null);
                    setOverStatus(null);
                  }}
                />
              ))}
              {items.length === 0 && <p className="board__empty">Trascina qui</p>}
            </div>
          </section>
        );
      })}
    </div>
  );
}
