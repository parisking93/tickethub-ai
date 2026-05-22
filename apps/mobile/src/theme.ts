import { TicketStatus } from '@tickethub/shared';

export const colors = {
  bg: '#0f1419',
  surface: '#1a2129',
  border: '#2e3946',
  text: '#e6edf3',
  textMuted: '#9aa7b4',
  primary: '#3b82f6',
};

export const statusColor: Record<TicketStatus, string> = {
  [TicketStatus.Creato]: '#6b7280',
  [TicketStatus.InLavorazione]: '#f59e0b',
  [TicketStatus.InAttesa]: '#8b5cf6',
  [TicketStatus.Approvato]: '#10b981',
  [TicketStatus.Concluso]: '#22c55e',
  [TicketStatus.Rifiutato]: '#ef4444',
};
