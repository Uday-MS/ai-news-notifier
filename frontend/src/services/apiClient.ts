/**
 * API Client — centralized HTTP wrapper with auth token management.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1';

interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: { code: string; message: string };
}

/** Get stored access token */
function getAccessToken(): string | null {
  return localStorage.getItem('access_token');
}

/** Get stored refresh token */
function getRefreshToken(): string | null {
  return localStorage.getItem('refresh_token');
}

/** Store tokens */
export function storeTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
}

/** Clear tokens */
export function clearTokens(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

/** Check if user has stored tokens */
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

/**
 * Core fetch wrapper with auth header injection and token refresh.
 */
export async function apiClient<T = unknown>(
  endpoint: string,
  options: RequestInit = {},
): Promise<ApiResponse<T>> {
  const headers = new Headers(options.headers);

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const accessToken = getAccessToken();
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Attempt token refresh on 401
  if (response.status === 401 && getRefreshToken()) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      headers.set('Authorization', `Bearer ${getAccessToken()}`);
      const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
      });
      return retryResponse.json();
    } else {
      clearTokens();
      window.location.href = '/login';
    }
  }

  return response.json();
}

async function tryRefreshToken(): Promise<boolean> {
  try {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) return false;

    const result = await response.json();
    if (result.success && result.data) {
      storeTokens(result.data.access_token, result.data.refresh_token);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}
