import { createApiClient } from '@tickethub/shared';

/** Istanza condivisa del client API, puntata al backend (via preload). */
export const api = createApiClient(() => window.tam?.backendUrl ?? 'http://127.0.0.1:8000');
