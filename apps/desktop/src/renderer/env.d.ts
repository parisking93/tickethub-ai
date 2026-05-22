/// <reference types="vite/client" />

import type { TamApi } from '../preload';

declare global {
  interface Window {
    tam: TamApi;
  }
}

export {};
