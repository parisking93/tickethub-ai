# integrations/email — Importazione email → ticket (Step 2)

Legge le email **non lette** di un account IMAP e crea un ticket per ognuna
(`type=email`, `status=creato`), deduplicando per `Message-ID`. Non modifica lo
stato della casella (apertura in sola lettura + `BODY.PEEK`).

## Moduli

| File | Ruolo |
|------|-------|
| `providers.py` | Preset host/porta IMAP e endpoint OAuth per gmail/icloud/outlook |
| `auth.py` | Strategie di login IMAP: password (basic) e OAuth2 (XOAUTH2) |
| `client.py` | `ImapEmailClient`: connessione, fetch dei messaggi non letti |
| `parser.py` | Email grezza (RFC 822) → `ParsedEmail` (subject, mittente, body, message-id) |
| `oauth/microsoft.py` | Flusso OAuth2 Authorization Code + PKCE per Microsoft |
| `oauth/state.py` | Store transitorio dello stato PKCE durante il redirect |

Logica a valle: `services/email_ingest_service.py` (crea i ticket) e
`services/email_account_service.py` (CRUD + OAuth). API in `api/v1/email.py`.

## Configurazione account per provider

### Gmail (password dedicata)
1. Attiva la **verifica in due passaggi** sull'account Google.
2. Crea una **App Password**: https://myaccount.google.com/apppasswords
3. Crea l'account in app con `provider=gmail`, `auth_type=password`, `secret=<app password>`.

### iCloud (password specifica per app)
1. Su https://account.apple.com → Sicurezza → **Password specifiche per app**.
2. Crea l'account con `provider=icloud`, `auth_type=password`, `secret=<password specifica>`.
   (Lo username IMAP è di norma la parte prima di `@` o l'email completa.)

### Outlook / Microsoft (OAuth2)
Il basic-auth IMAP è disabilitato da Microsoft: serve OAuth2.

1. Vai su **Azure Portal → Microsoft Entra ID → App registrations → New registration**.
   - Supported account types: *Personal Microsoft accounts* (o anche aziendali).
   - **Redirect URI** (tipo *Web*): `http://localhost:8000/api/v1/email/oauth/callback`
2. Dalla scheda **Overview** copia l'**Application (client) ID**.
3. In **API permissions** aggiungi (delegated): `IMAP.AccessAsUser.All` e `offline_access`.
4. Metti il client_id in `MS_OAUTH_CLIENT_ID` (in `.env`) **oppure** passalo per account.
5. Crea l'account con `provider=outlook`, `auth_type=oauth2`, poi avvia
   `POST /email/accounts/{id}/oauth/start`, apri l'`authorize_url`, accedi: il
   refresh token viene salvato e l'account risulta `is_authorized=true`.

## Sincronizzazione

- `POST /api/v1/email/sync` → sincronizza tutti gli account attivi.
- `POST /api/v1/email/sync?account_id=<id>` → un solo account.

Il polling automatico (job che gira da solo) arriverà con lo **Step 3** (job worker).
