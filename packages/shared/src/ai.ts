/**
 * Contratti condivisi per i profili AI.
 * Allineati con backend/src/app/schemas/ai_profile.py.
 */

export type AIProvider = 'ollama' | 'lmstudio' | 'openai_compatible';

/** Operazioni che possono avere un modello dedicato. */
export type AIOperation = 'email' | 'fix' | 'feature' | 'vision';

export interface AIProfile {
  id: number;
  name: string;
  provider: AIProvider;
  base_url: string | null;
  model_email: string;
  model_fix: string;
  model_feature: string;
  model_vision: string;
  is_active: boolean;
  has_api_key: boolean;
}

export interface CreateAIProfileInput {
  name: string;
  provider?: AIProvider;
  base_url?: string | null;
  api_key?: string | null;
  model_email?: string;
  model_fix?: string;
  model_feature?: string;
  model_vision?: string;
}

export interface UpdateAIProfileInput {
  name?: string;
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
