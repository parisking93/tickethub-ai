# apps/mobile — App mobile (Expo + React Native)

Gestione ticket da cellulare. Si connette al **backend desktop** sulla LAN (col PC
acceso) e riusa gli stessi contratti e client API di `@tickethub/shared`.

## Cosa fa (Step 6)
- **Board**: elenco dei ticket con stato, pull-to-refresh, pulsante **▶ Job** (avvia l'AI worker).
- **Dettaglio ticket**: mostra nota e bozza/piano dell'AI; azioni rapide (in lavorazione,
  approva, rifiuta con nota, concludi).
- **Impostazioni**: URL del backend desktop (persistito) + "Verifica connessione".

## Avvio (richiede Node + Expo)
```bash
cd apps/mobile
npm install
npm start            # apre Expo; usa Expo Go sul telefono o un emulatore
```

> Questo è uno scaffold: le dipendenze (Expo/React Native) non sono installate nel
> repo. Esegui `npm install` qui prima di avviare. La `metro.config.js` è già
> configurata per il monorepo (risolve `@tickethub/shared` dalla root).

## Collegare il telefono al desktop
1. Avvia il backend in ascolto sulla rete (non solo su localhost):
   ```bash
   uvicorn app.main:app --app-dir src --host 0.0.0.0 --port 8000
   ```
   (oppure imposta `API_HOST=0.0.0.0` nel `.env`).
2. Trova l'IP del PC sulla LAN (es. `192.168.1.50`).
3. Telefono e PC sulla **stessa rete Wi-Fi**; consenti la porta 8000 nel firewall di Windows.
4. Nell'app → **⚙ Impostazioni** → inserisci `http://192.168.1.50:8000` → **Verifica connessione**.

> Nota: le app native non sono soggette alle restrizioni CORS del browser, quindi non
> serve configurare le origini per il mobile.

## Struttura
```
src/
├── api/client.ts        # createApiClient(@tickethub/shared) con URL dinamico
├── config/backend.ts    # URL backend persistito (AsyncStorage)
├── theme.ts             # colori e colori-per-stato condivisi con la UI desktop
├── App.tsx              # navigazione (Board / Dettaglio / Impostazioni)
└── screens/             # BoardScreen, TicketDetailScreen, SettingsScreen
```
