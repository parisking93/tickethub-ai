import AsyncStorage from '@react-native-async-storage/async-storage';

/**
 * URL del backend desktop a cui connettersi (sulla LAN, col PC acceso).
 * Es. http://192.168.1.50:8000 — il backend deve ascoltare su 0.0.0.0.
 */
const STORAGE_KEY = 'tickethub.backendUrl';
const DEFAULT_URL = 'http://192.168.1.50:8000';

let current = DEFAULT_URL;

export async function loadBackendUrl(): Promise<string> {
  const stored = await AsyncStorage.getItem(STORAGE_KEY);
  if (stored) current = stored;
  return current;
}

export async function setBackendUrl(url: string): Promise<void> {
  current = url.replace(/\/+$/, '');
  await AsyncStorage.setItem(STORAGE_KEY, current);
}

export function getBackendUrl(): string {
  return current;
}
