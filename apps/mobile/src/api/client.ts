import { createApiClient } from '@tickethub/shared';
import { getBackendUrl } from '../config/backend';

/**
 * Stesso client API del desktop: l'URL è risolto dinamicamente dalle impostazioni,
 * così punta al backend desktop sulla LAN.
 */
export const api = createApiClient(() => getBackendUrl());
