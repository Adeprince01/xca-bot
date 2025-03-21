// xca-bot/lib/api.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Define types for API responses
export interface StatusResponse {
  is_running: boolean;
  pid?: number;
  uptime?: string;
  monitored_users: number;
  regex_patterns: number;
  keywords: number;
  check_interval: number;
  last_check?: string;
}

export interface Match {
  username: string;
  tweet_id: string;
  tweet_text: string;
  matched_pattern: string[];
  timestamp: string;
  tweet_url: string;
}

export interface MatchesResponse {
  matches: Match[];
  total: number;
}

export interface MessageResponse {
  message: string;
  success: boolean;
}

export interface TwitterConfig {
  api_key: string;
  api_secret: string;
  access_token: string;
  access_token_secret: string;
}

export interface TelegramConfig {
  bot_token: string;
  channel_id: string;
  enable_direct_messages: boolean;
  include_tweet_text: boolean;
}

export interface MonitoringConfig {
  check_interval_minutes: number;
  usernames: string[];
  regex_patterns: string[];
  keywords: string[];
}

export interface FullConfig {
  twitter: TwitterConfig;
  telegram: TelegramConfig;
  monitoring: MonitoringConfig;
}

// Helper function to handle API errors
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    // Try to get error details from response
    try {
      const errorData = await response.json();
      throw new Error(errorData.detail || `API error: ${response.status}`);
    } catch (e) {
      // If parsing JSON fails, use status text
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
  }
  return response.json() as Promise<T>;
}

// API functions with proper typing
export async function fetchStatus(): Promise<StatusResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/status`);
    return handleResponse<StatusResponse>(response);
  } catch (error) {
    console.error('Error fetching status:', error);
    throw new Error('Failed to fetch status: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function startMonitoring(): Promise<MessageResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/start`, {
      method: 'POST',
    });
    return handleResponse<MessageResponse>(response);
  } catch (error) {
    console.error('Error starting monitoring:', error);
    throw new Error('Failed to start monitoring: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function stopMonitoring(): Promise<MessageResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/stop`, {
      method: 'POST',
    });
    return handleResponse<MessageResponse>(response);
  } catch (error) {
    console.error('Error stopping monitoring:', error);
    throw new Error('Failed to stop monitoring: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function fetchConfig(): Promise<FullConfig> {
  try {
    const response = await fetch(`${API_BASE_URL}/config`);
    return handleResponse<FullConfig>(response);
  } catch (error) {
    console.error('Error fetching configuration:', error);
    throw new Error('Failed to fetch configuration: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function updateConfig(config: FullConfig): Promise<MessageResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
    return handleResponse<MessageResponse>(response);
  } catch (error) {
    console.error('Error updating configuration:', error);
    throw new Error('Failed to update configuration: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function fetchMatches(limit = 10): Promise<MatchesResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/matches?limit=${limit}`);
    return handleResponse<MatchesResponse>(response);
  } catch (error) {
    console.error('Error fetching matches:', error);
    throw new Error('Failed to fetch matches: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function checkNow(): Promise<MessageResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/check`, {
      method: 'POST',
    });
    return handleResponse<MessageResponse>(response);
  } catch (error) {
    console.error('Error starting check:', error);
    throw new Error('Failed to start check: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function fetchUsers(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/users`);
    return handleResponse<string[]>(response);
  } catch (error) {
    console.error('Error fetching users:', error);
    throw new Error('Failed to fetch users: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function updateUsers(users: string[]): Promise<MessageResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(users),
    });
    return handleResponse<MessageResponse>(response);
  } catch (error) {
    console.error('Error updating users:', error);
    throw new Error('Failed to update users: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function fetchPatterns(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/patterns`);
    return handleResponse<string[]>(response);
  } catch (error) {
    console.error('Error fetching patterns:', error);
    throw new Error('Failed to fetch patterns: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function updatePatterns(patterns: string[]): Promise<MessageResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/patterns`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(patterns),
    });
    return handleResponse<MessageResponse>(response);
  } catch (error) {
    console.error('Error updating patterns:', error);
    throw new Error('Failed to update patterns: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function fetchKeywords(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/keywords`);
    return handleResponse<string[]>(response);
  } catch (error) {
    console.error('Error fetching keywords:', error);
    throw new Error('Failed to fetch keywords: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function updateKeywords(keywords: string[]): Promise<MessageResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/keywords`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(keywords),
    });
    return handleResponse<MessageResponse>(response);
  } catch (error) {
    console.error('Error updating keywords:', error);
    throw new Error('Failed to update keywords: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function exportMatches(filename = 'matches_export.csv'): Promise<MessageResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ filename }),
    });
    return handleResponse<MessageResponse>(response);
  } catch (error) {
    console.error('Error exporting matches:', error);
    throw new Error('Failed to export matches: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function cleanupDatabase(): Promise<MessageResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/cleanup`, {
      method: 'POST',
    });
    return handleResponse<MessageResponse>(response);
  } catch (error) {
    console.error('Error cleaning up database:', error);
    throw new Error('Failed to clean up database: ' + (error instanceof Error ? error.message : String(error)));
  }
}

export async function fetchLogs(limit = 100): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/logs?limit=${limit}`);
    return handleResponse<string[]>(response);
  } catch (error) {
    console.error('Error fetching logs:', error);
    throw new Error('Failed to fetch logs: ' + (error instanceof Error ? error.message : String(error)));
  }
}

// New utility functions

// Retry a failed API call with exponential backoff
export async function retryWithBackoff<T>(
  fn: () => Promise<T>, 
  maxRetries = 3, 
  initialDelay = 1000
): Promise<T> {
  let retries = 0;
  
  while (true) {
    try {
      return await fn();
    } catch (error) {
      if (retries >= maxRetries) {
        throw error;
      }
      
      const delay = initialDelay * Math.pow(2, retries);
      console.log(`Retrying after ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
      retries++;
    }
  }
}

// Check if the API is available
export async function checkApiAvailability(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/`);
    return response.ok;
  } catch (error) {
    console.error('API server is not available:', error);
    return false;
  }
}