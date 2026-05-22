/**
 * Contratti condivisi tra desktop e mobile.
 * Devono restare allineati con gli enum del backend (backend/src/app/models/ticket.py).
 */

/** Stati del ciclo di vita di un ticket. */
export enum TicketStatus {
  Creato = 'creato',
  InLavorazione = 'in_lavorazione',
  InAttesa = 'in_attesa',
  Approvato = 'approvato',
  Concluso = 'concluso',
  Rifiutato = 'rifiutato',
}

/** Tipo di ticket: determina come l'AI lo lavora. */
export enum TicketType {
  Email = 'email',
  Fix = 'fix',
  Feature = 'feature',
}

/** Origine del ticket. */
export enum TicketSource {
  Manuale = 'manuale',
  Email = 'email',
  Odoo = 'odoo',
}

/** Ordine di visualizzazione delle colonne nella board. */
export const STATUS_ORDER: TicketStatus[] = [
  TicketStatus.Creato,
  TicketStatus.InLavorazione,
  TicketStatus.InAttesa,
  TicketStatus.Approvato,
  TicketStatus.Concluso,
];

/** Etichette leggibili (IT) per la UI. */
export const STATUS_LABELS: Record<TicketStatus, string> = {
  [TicketStatus.Creato]: 'Creato',
  [TicketStatus.InLavorazione]: 'In lavorazione',
  [TicketStatus.InAttesa]: 'In attesa',
  [TicketStatus.Approvato]: 'Approvato',
  [TicketStatus.Concluso]: 'Concluso',
  [TicketStatus.Rifiutato]: 'Rifiutato',
};

export const TYPE_LABELS: Record<TicketType, string> = {
  [TicketType.Email]: 'Email',
  [TicketType.Fix]: 'Fix',
  [TicketType.Feature]: 'Feature',
};

export interface Ticket {
  id: number;
  title: string;
  description: string | null;
  type: TicketType;
  status: TicketStatus;
  source: TicketSource;
  /** Nota dell'AI mostrata all'utente (es. "va approvata l'email"). */
  ai_note: string | null;
  /** Output dell'AI da rivedere: bozza email o piano di modifica. */
  ai_draft: string | null;
  /** Nota dell'utente in caso di rifiuto/revisione. */
  review_note: string | null;
  branch_name: string | null;
  external_ref: string | null;
  /** Per i ticket email: indirizzo a cui rispondere e account di provenienza. */
  source_address: string | null;
  email_account_id: number | null;
  /** Per i ticket fix/feature: progetto git su cui lavorare. */
  project_id: number | null;
  created_at: string;
  updated_at: string;
}

/** Esito di un giro del job worker. */
export interface JobRunResult {
  processed: number;
  finalized: number;
  results: { ticket_id: number; action: string; status: string; note: string }[];
  errors: string[];
}

/** Payload per creare un ticket. */
export interface CreateTicketInput {
  title: string;
  description?: string | null;
  type: TicketType;
  source?: TicketSource;
  external_ref?: string | null;
  project_id?: number | null;
}

/** Payload per aggiornare lo stato (con eventuale nota di revisione). */
export interface UpdateTicketStatusInput {
  status: TicketStatus;
  review_note?: string | null;
}
