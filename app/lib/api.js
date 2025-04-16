/**
 * API integration for XCA-Bot frontend
 */
import getNextConfig from 'next/config';

// Safely get runtime configuration (works in both SSR and client side)
const getConfigSafe = () => {
  try {
    // This will throw during SSR if not properly configured
    return getNextConfig() || {};
  } catch (e) {
    console.warn('Warning: Could not load Next.js config - using defaults', e);
    return { publicRuntimeConfig: {} };
  }
};

// Get runtime configuration with fallbacks
const { publicRuntimeConfig = {} } = getConfigSafe();

// API base URL - use environment variable with fallback
const API_BASE_URL = publicRuntimeConfig.apiBaseUrl || 
                    (typeof window !== 'undefined' && window.env?.API_BASE_URL) || 
                    (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_BASE_URL) || 
                    'http://127.0.0.1:8000/api/v1';

// Disable mock data usage completely for production
const USE_MOCK_DATA_FALLBACK = false;

// Enable more detailed logging
const VERBOSE_LOGGING = typeof process !== 'undefined' && process.env.NODE_ENV === 'development';

/**
 * Logger utility for the API client
 */
const logger = {
  info: (message) => {
    if (VERBOSE_LOGGING) console.info(`[XCA-API] ${message}`);
  },
  warn: (message, error) => {
    console.warn(`[XCA-API] ⚠️ ${message}`, error);
  },
  error: (message, error) => {
    console.error(`[XCA-API] 🔴 ${message}`, error);
  }
};

/**
 * Makes an HTTP request to the API
 * @param {string} endpoint - API endpoint path
 * @param {Object} options - fetch options
 * @returns {Promise<any>} - API response
 */
async function makeApiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  // Set default headers if not provided
  if (!options.headers) {
    options.headers = {
      'Content-Type': 'application/json'
    };
  }
  
  logger.info(`Calling API: ${options.method || 'GET'} ${url}`);
  
  try {
    // Create an AbortController for request timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    
    // Clear the timeout
    clearTimeout(timeoutId);
    
    // Check if the response is ok
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP Error ${response.status}: ${errorText}`);
    }
    
    // Parse JSON response
    const data = await response.json();
    return data;
  } catch (error) {
    // Improve error messages for common connection issues
    if (error.name === 'AbortError') {
      throw new Error(`Request timeout: API server at ${API_BASE_URL} took too long to respond.`);
    } else if (error.message === 'Failed to fetch') {
      throw new Error(`Cannot connect to API server at ${API_BASE_URL}. Make sure the server is running and accessible.`);
    } else if (error.message.includes('NetworkError')) {
      throw new Error(`Network error: Unable to connect to ${API_BASE_URL}. Check your internet connection and server status.`);
    }
    
    logger.error(`API request to ${url} failed`, error);
    throw error;
  }
}

/**
 * Fetches the current monitoring status
 * @returns {Promise<Object>} Status information
 */
export async function fetchStatus() {
  try {
    const status = await makeApiRequest('/status');
    logger.info('Successfully fetched status');
    return status;
  } catch (error) {
    logger.error('Failed to fetch status', error);
    throw error;
  }
}

/**
 * Starts the monitoring service
 * @returns {Promise<Object>} Updated status
 */
export async function startMonitoring() {
  try {
    const result = await makeApiRequest('/monitoring/start', { method: 'POST' });
    logger.info('Successfully started monitoring');
    return result;
  } catch (error) {
    logger.error('Failed to start monitoring', error);
    throw error;
  }
}

/**
 * Stops the monitoring service
 * @returns {Promise<Object>} Updated status
 */
export async function stopMonitoring() {
  try {
    const result = await makeApiRequest('/monitoring/stop', { method: 'POST' });
    logger.info('Successfully stopped monitoring');
    return result;
  } catch (error) {
    logger.error('Failed to stop monitoring', error);
    throw error;
  }
}

/**
 * Triggers an immediate check for crypto addresses
 * @returns {Promise<Object>} Check results
 */
export async function checkNow() {
  try {
    const result = await makeApiRequest('/check', { method: 'POST' });
    logger.info('Successfully triggered check');
    return result;
  } catch (error) {
    logger.error('Failed to trigger check', error);
    throw error;
  }
}

/**
 * Retrieves matched crypto addresses
 * @param {number} limit - Maximum number of matches to return
 * @returns {Promise<Array>} List of matches
 */
export async function getMatches(limit = 20) {
  try {
    const data = await makeApiRequest(`/matches?limit=${limit}`);
    logger.info(`Successfully fetched ${data.length || 0} matches`);
    return data;
  } catch (error) {
    logger.error('Failed to fetch matches', error);
    throw error;
  }
}

/**
 * Retrieves current configuration
 * @returns {Promise<Object>} Configuration object
 */
export async function getConfig() {
  try {
    const config = await makeApiRequest('/config');
    logger.info('Successfully fetched configuration');
    return config;
  } catch (error) {
    logger.error('Failed to fetch configuration', error);
    throw error;
  }
}

/**
 * Updates the configuration
 * @param {Object} configData - New configuration data
 * @returns {Promise<Object>} Update result
 */
export async function updateConfig(configData) {
  try {
    const result = await makeApiRequest('/config', {
      method: 'PUT',
      body: JSON.stringify(configData)
    });
    logger.info('Successfully updated configuration');
    return result;
  } catch (error) {
    logger.error('Failed to update configuration', error);
    throw error;
  }
}

/**
 * Tests the Telegram configuration
 * @param {string} chatId - Telegram chat ID to test
 * @returns {Promise<Object>} Test result
 */
export async function testTelegramConfig(chatId) {
  try {
    const result = await makeApiRequest(`/telegram/test/${chatId}`, {
      method: 'POST'
    });
    logger.info(`Successfully tested Telegram config for chat ${chatId}`);
    return result;
  } catch (error) {
    logger.error(`Failed to test Telegram config for chat ${chatId}`, error);
    throw error;
  }
}

/**
 * Adds a new Telegram destination
 * @param {string} chatId - Telegram chat ID
 * @param {string|null} description - Optional description
 * @returns {Promise<Object>} Result
 */
export async function addTelegramDestination(chatId, description = null) {
  try {
    const payload = { chat_id: chatId };
    if (description) {
      payload.description = description;
    }
    
    const result = await makeApiRequest('/telegram/destinations', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    
    logger.info(`Successfully added Telegram destination ${chatId}`);
    return result;
  } catch (error) {
    logger.error(`Failed to add Telegram destination ${chatId}`, error);
    throw error;
  }
}

/**
 * Removes a Telegram destination
 * @param {string} chatId - Telegram chat ID to remove
 * @returns {Promise<Object>} Result
 */
export async function removeTelegramDestination(chatId) {
  try {
    const result = await makeApiRequest(`/telegram/destinations/${chatId}`, {
      method: 'DELETE'
    });
    
    logger.info(`Successfully removed Telegram destination ${chatId}`);
    return result;
  } catch (error) {
    logger.error(`Failed to remove Telegram destination ${chatId}`, error);
    throw error;
  }
}

/**
 * Tests a specific Telegram destination
 * @param {string} chatId - Telegram chat ID to test
 * @returns {Promise<Object>} Test result
 */
export async function testTelegramDestination(chatId) {
  try {
    const result = await makeApiRequest(`/telegram/destinations/${chatId}/test`, {
      method: 'POST'
    });
    
    logger.info(`Successfully tested Telegram destination ${chatId}`);
    return result;
  } catch (error) {
    logger.error(`Failed to test Telegram destination ${chatId}`, error);
    throw error;
  }
} 