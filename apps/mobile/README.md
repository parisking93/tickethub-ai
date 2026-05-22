# apps/mobile — React Native (Step 6)

App mobile che si connette al **backend desktop** via API (lo stesso FastAPI di
`backend/`), così da gestire i ticket dal cellulare lasciando il PC acceso.

Riuserà i contratti TypeScript di `packages/shared` (stati, tipi, interfacce
`Ticket`), per non duplicare la logica già usata dal desktop.

Da definire allo Step 6:

- Scaffold React Native (Expo o bare).
- Discovery/sync del backend desktop (URL configurabile, eventuale tunnel/LAN).
- Autenticazione device ↔ desktop.
