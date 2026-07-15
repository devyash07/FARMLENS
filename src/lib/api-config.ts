/**
 * API Configuration
 * Centralized API URL management for different environments
 */

export const API_CONFIG = {
  // Use environment variable or fall back to localhost
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  
  // API endpoints
  ENDPOINTS: {
    ANALYZE: '/analyze',
    HISTORY: '/history',
    FEEDBACK: '/feedback',
    CHATBOT: '/api/chatbot/chat',
    CHATBOT_HEALTH: '/api/chatbot/health',
  },
  
  // Request timeout (30 seconds)
  TIMEOUT: 30000,
  
  // Image upload limits
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ACCEPTED_FORMATS: ['image/jpeg', 'image/png', 'image/webp'],
} as const;

/**
 * Get full API URL for an endpoint
 */
export function getApiUrl(endpoint: keyof typeof API_CONFIG.ENDPOINTS): string {
  return `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS[endpoint]}`;
}

/**
 * Check if running in production
 */
export function isProduction(): boolean {
  return import.meta.env.PROD;
}

/**
 * Get app version
 */
export function getAppVersion(): string {
  return import.meta.env.VITE_APP_VERSION || '1.0.0';
}
