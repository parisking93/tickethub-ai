import { TicketStatus } from '@tickethub/shared';

/**
 * Transizioni ammesse lato UI — specchio di ALLOWED_TRANSITIONS del backend
 * (backend/src/app/services/ticket_service.py). Servono solo a mostrare i
 * pulsanti di azione corretti; la validazione autorevole resta sul backend.
 */
export const ALLOWED_TRANSITIONS: Record<TicketStatus, TicketStatus[]> = {
  [TicketStatus.Creato]: [TicketStatus.InLavorazione],
  [TicketStatus.InLavorazione]: [TicketStatus.InAttesa, TicketStatus.Concluso],
  [TicketStatus.InAttesa]: [TicketStatus.Approvato, TicketStatus.Rifiutato],
  [TicketStatus.Approvato]: [TicketStatus.Concluso, TicketStatus.InLavorazione],
  [TicketStatus.Rifiutato]: [TicketStatus.InLavorazione],
  [TicketStatus.Concluso]: [],
};
