/**
 * API Service for Frontend
 * Handles all API calls to the backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || `http://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:8009`;

export class ApiService {
  /**
   * Get analytics statistics
   */
  static async getAnalytics() {
    const response = await fetch(`${API_BASE_URL}/api/analytics`);
    if (!response.ok) throw new Error('Failed to fetch analytics');
    return response.json();
  }

  /**
   * Export conversation
   */
  static async exportConversation(sessionId: string, conversationHistory: any[], format: 'json' | 'text' | 'markdown' = 'json') {
    const response = await fetch(`${API_BASE_URL}/api/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, conversation_history: conversationHistory, format })
    });
    if (!response.ok) throw new Error('Export failed');
    return response.json();
  }

  /**
   * Get available models
   */
  static async getModels() {
    const response = await fetch(`${API_BASE_URL}/api/models`);
    if (!response.ok) throw new Error('Failed to fetch models');
    return response.json();
  }

  /**
   * Execute a tool
   */
  static async executeTool(toolName: string, parameters: any) {
    const response = await fetch(`${API_BASE_URL}/api/tools/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_name: toolName, parameters })
    });
    if (!response.ok) throw new Error('Tool execution failed');
    return response.json();
  }

  /**
   * Add knowledge to RAG
   */
  static async addKnowledge(topic: string, content: string, metadata?: any) {
    const response = await fetch(`${API_BASE_URL}/api/rag/knowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, content, metadata })
    });
    if (!response.ok) throw new Error('Failed to add knowledge');
    return response.json();
  }

  /**
   * Get RAG statistics
   */
  static async getRagStats() {
    const response = await fetch(`${API_BASE_URL}/api/rag/stats`);
    if (!response.ok) throw new Error('Failed to fetch RAG stats');
    return response.json();
  }

  /**
   * Get user preferences
   */
  static async getPreferences() {
    const response = await fetch(`${API_BASE_URL}/api/preferences`);
    if (!response.ok) throw new Error('Failed to fetch preferences');
    return response.json();
  }

  /**
   * Update user preferences
   */
  static async updatePreferences(preferences: any) {
    const response = await fetch(`${API_BASE_URL}/api/preferences`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(preferences)
    });
    if (!response.ok) throw new Error('Failed to update preferences');
    return response.json();
  }

  /**
   * Get a specific preference
   */
  static async getPreference(category: string, key: string) {
    const response = await fetch(`${API_BASE_URL}/api/preferences/${category}/${key}`);
    if (!response.ok) throw new Error('Failed to fetch preference');
    return response.json();
  }

  /**
   * Reset preferences to defaults
   */
  static async resetPreferences() {
    const response = await fetch(`${API_BASE_URL}/api/preferences/reset`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to reset preferences');
    return response.json();
  }
}

