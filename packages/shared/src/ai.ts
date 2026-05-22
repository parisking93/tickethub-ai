/**
 * Contratti condivisi per la configurazione AI.
 * Allineati con backend/src/app/schemas/ai_settings.py.
 */

export type AIProvider = 'ollama' | 'lmstudio' | 'openai_compatible';

/** Operazioni che possono avere un modello dedicato. */
export type AIOperation = 'email' | 'fix' | 'feature' | 'vision';

export interface AISettings {
  provider: AIProvider;
  base_url: string | null;
  model_email: string;
  model_fix: string;
  model_feature: string;
  model_vision: string;
  has_api_key: boolean;
}

export interface UpdateAISettingsInput {
  provider?: AIProvider;
  base_url?: string | null;
  api_key?: string | null;
  model_email?: string;
  model_fix?: string;
  model_feature?: string;
  model_vision?: string;
}

export interface ModelList {
  provider: string;
  models: string[];
}
