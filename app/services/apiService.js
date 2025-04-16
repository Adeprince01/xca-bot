import { getMockStatus, getMockMatches, getMockConfig } from '../utils/mockData';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
const USE_MOCK = false; // Force to false regardless of environment variable

// Helper function to handle API calls without mock fallback
async function apiCall(endpoint, options = {}) {
  try {
    // Create an AbortController for the timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      signal: controller.signal
    });
    
    // Clear the timeout
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    // Enhance error messages for common connection issues
    if (error.name === 'AbortError') {
      throw new Error(`Request timeout: API server at ${API_BASE_URL} took too long to respond.`);
    } else if (error.message === 'Failed to fetch') {
      throw new Error(`Cannot connect to API server at ${API_BASE_URL}. Please check that the backend server is running.`);
    }

    console.error(`API call failed: ${error.message}`);
    throw error;
  }
}

// API methods
export const getStatus = () => {
  return apiCall('/status', { method: 'GET' });
};

export const getMatches = (page = 1, perPage = 10) => {
  return apiCall(`/matches?page=${page}&per_page=${perPage}`, { method: 'GET' });
};

export const getConfig = () => {
  return apiCall('/config', { method: 'GET' });
};

export const updateConfig = (config) => {
  return apiCall('/config', {
    method: 'PUT',
    body: JSON.stringify(config),
  });
};

export const startMonitoring = () => {
  return apiCall('/monitoring/start', {
    method: 'POST',
  });
};

export const stopMonitoring = () => {
  return apiCall('/monitoring/stop', {
    method: 'POST',
  });
};

export const checkNow = () => {
  return apiCall('/check', {
    method: 'POST',
  });
}; 