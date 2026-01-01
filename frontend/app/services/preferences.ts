/**
 * Preferences Service for Frontend
 * Manages user preferences with localStorage persistence
 */

import { ApiService } from './api';

export interface UserPreferences {
  audio: {
    sample_rate: number;
    quality: 'low' | 'medium' | 'high';
    format: 'wav' | 'mp3' | 'ogg';
  };
  ui: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    animations: boolean;
  };
  llm: {
    default_model: string;
    temperature: number;
    max_tokens: number;
  };
  features: {
    vad_enabled: boolean;
    emotion_detection: boolean;
    translation: boolean;
    rag_enabled: boolean;
    tools_enabled: boolean;
  };
  connection: {
    auto_reconnect: boolean;
    reconnect_delay: number;
    max_retries: number;
  };
  updated_at?: string;
}

const PREFERENCES_KEY = 'whisperbrain_preferences';

export class PreferencesService {
  private static preferences: UserPreferences | null = null;

  /**
   * Load preferences from localStorage or API
   */
  static async loadPreferences(): Promise<UserPreferences> {
    // Try localStorage first
    const stored = localStorage.getItem(PREFERENCES_KEY);
    if (stored) {
      try {
        this.preferences = JSON.parse(stored);
        // Sync with server in background
        this.syncWithServer().catch(console.error);
        return this.preferences;
      } catch (e) {
        console.warn('Failed to parse stored preferences', e);
      }
    }

    // Load from server
    try {
      this.preferences = await ApiService.getPreferences();
      this.saveToLocalStorage();
      return this.preferences;
    } catch (e) {
      console.error('Failed to load preferences from server', e);
      // Return defaults
      return this.getDefaultPreferences();
    }
  }

  /**
   * Get current preferences (load if needed)
   */
  static async getPreferences(): Promise<UserPreferences> {
    if (!this.preferences) {
      return await this.loadPreferences();
    }
    return this.preferences;
  }

  /**
   * Update preferences
   */
  static async updatePreferences(updates: Partial<UserPreferences>): Promise<UserPreferences> {
    const current = await this.getPreferences();
    this.preferences = {
      ...current,
      ...updates,
      updated_at: new Date().toISOString()
    };

    // Save to localStorage immediately
    this.saveToLocalStorage();

    // Sync with server
    try {
      await ApiService.updatePreferences(updates);
    } catch (e) {
      console.error('Failed to sync preferences with server', e);
    }

    return this.preferences;
  }

  /**
   * Get a specific preference value
   */
  static async getPreference<T>(
    category: keyof UserPreferences,
    key: string,
    defaultValue?: T
  ): Promise<T> {
    const prefs = await this.getPreferences();
    const categoryPrefs = prefs[category] as any;
    return (categoryPrefs?.[key] ?? defaultValue) as T;
  }

  /**
   * Set a specific preference value
   */
  static async setPreference(
    category: keyof UserPreferences,
    key: string,
    value: any
  ): Promise<void> {
    const current = await this.getPreferences();
    const categoryPrefs = { ...(current[category] as any) };
    categoryPrefs[key] = value;

    await this.updatePreferences({
      [category]: categoryPrefs
    } as any);
  }

  /**
   * Reset to defaults
   */
  static async resetPreferences(): Promise<UserPreferences> {
    try {
      this.preferences = await ApiService.resetPreferences();
      this.saveToLocalStorage();
      return this.preferences;
    } catch (e) {
      console.error('Failed to reset preferences', e);
      this.preferences = this.getDefaultPreferences();
      this.saveToLocalStorage();
      return this.preferences;
    }
  }

  /**
   * Sync preferences with server
   */
  private static async syncWithServer(): Promise<void> {
    if (!this.preferences) return;

    try {
      await ApiService.updatePreferences(this.preferences);
    } catch (e) {
      console.warn('Failed to sync preferences with server', e);
    }
  }

  /**
   * Save to localStorage
   */
  private static saveToLocalStorage(): void {
    if (this.preferences) {
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(this.preferences));
    }
  }

  /**
   * Get default preferences
   */
  static getDefaultPreferences(): UserPreferences {
    return {
      audio: {
        sample_rate: 16000,
        quality: 'medium',
        format: 'wav'
      },
      ui: {
        theme: 'light',
        language: 'en',
        animations: true
      },
      llm: {
        default_model: 'phi3:mini',
        temperature: 0.7,
        max_tokens: 1000
      },
      features: {
        vad_enabled: true,
        emotion_detection: true,
        translation: false,
        rag_enabled: false,
        tools_enabled: false
      },
      connection: {
        auto_reconnect: true,
        reconnect_delay: 3,
        max_retries: 5
      }
    };
  }
}

