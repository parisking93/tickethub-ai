/**
 * Contratti condivisi per le connessioni Odoo.
 * Allineati con backend/src/app/models/odoo_connection.py e schemas/odoo_connection.py.
 */

import type { TicketType } from './ticket';

export interface OdooConnection {
  id: number;
  name: string;
  url: string;
  db_name: string;
  username: string;
  ticket_model: string;
  default_type: TicketType;
  project_id: number | null;
  active: boolean;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
  has_secret: boolean;
}

export interface CreateOdooConnectionInput {
  name: string;
  url: string;
  db_name: string;
  username: string;
  secret: string;
  ticket_model?: string;
  default_type?: TicketType;
  project_id?: number | null;
}

export interface OdooSyncResult {
  connection_id: number;
  fetched: number;
  created: number;
  skipped: number;
  errors: string[];
}
