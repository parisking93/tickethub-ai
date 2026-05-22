/**
 * Contratti condivisi per gli account email.
 * Allineati con backend/src/app/models/email_account.py e schemas/email_account.py.
 */

export enum EmailProvider {
  Gmail = 'gmail',
  ICloud = 'icloud',
  Outlook = 'outlook',
  Imap = 'imap',
}

export enum EmailAuthType {
  Password = 'password',
  OAuth2 = 'oauth2',
}

export const PROVIDER_LABELS: Record<EmailProvider, string> = {
  [EmailProvider.Gmail]: 'Gmail',
  [EmailProvider.ICloud]: 'iCloud',
  [EmailProvider.Outlook]: 'Outlook',
  [EmailProvider.Imap]: 'IMAP generico',
};

/** Auth di default suggerita per provider (Outlook richiede OAuth2). */
export const DEFAULT_AUTH: Record<EmailProvider, EmailAuthType> = {
  [EmailProvider.Gmail]: EmailAuthType.Password,
  [EmailProvider.ICloud]: EmailAuthType.Password,
  [EmailProvider.Outlook]: EmailAuthType.OAuth2,
  [EmailProvider.Imap]: EmailAuthType.Password,
};

export interface EmailAccount {
  id: number;
  email: string;
  display_name: string | null;
  provider: EmailProvider;
  auth_type: EmailAuthType;
  imap_host: string;
  imap_port: number;
  folder: string;
  active: boolean;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
  has_secret: boolean;
  is_authorized: boolean;
}

export interface CreateEmailAccountInput {
  email: string;
  display_name?: string | null;
  provider: EmailProvider;
  auth_type: EmailAuthType;
  imap_host?: string | null;
  imap_port?: number | null;
  username?: string | null;
  folder?: string;
  secret?: string | null;
  oauth_client_id?: string | null;
}

export interface EmailSyncResult {
  account_id: number;
  fetched: number;
  created: number;
  skipped: number;
  errors: string[];
}
