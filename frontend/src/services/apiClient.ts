/**
 * API Client — centralized HTTP wrapper with auth token management.
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.PROD ? '/api/v1' : 'http://localhost:8000/api/v1');

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

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
  } catch {
    return { success: false, error: { code: 'NETWORK_ERROR', message: 'Network error. Please check your connection.' } };
  }

  // Attempt token refresh on 401
  if (response.status === 401 && getRefreshToken()) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      headers.set('Authorization', `Bearer ${getAccessToken()}`);
      try {
        const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
          ...options,
          headers,
        });
        return await parseResponse<T>(retryResponse);
      } catch {
        return { success: false, error: { code: 'NETWORK_ERROR', message: 'Network error on retry.' } };
      }
    } else {
      clearTokens();
      window.location.href = '/login';
      return { success: false, error: { code: 'AUTH_EXPIRED', message: 'Session expired.' } };
    }
  }

  return parseResponse<T>(response);
}

/** Safely parse JSON response, handling non-JSON error bodies. */
async function parseResponse<T>(response: Response): Promise<ApiResponse<T>> {
  try {
    const body = await response.json();
    return body as ApiResponse<T>;
  } catch {
    return {
      success: false,
      error: {
        code: `HTTP_${response.status}`,
        message: response.statusText || 'An unexpected error occurred.',
      },
    };
  }
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
