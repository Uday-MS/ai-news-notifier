/**
 * Authentication service — API calls for auth endpoints.
 */

import { apiClient, storeTokens, clearTokens } from './apiClient';

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_verified: boolean;
  created_at: string;
}

export interface TokenData {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export async function registerUser(
  email: string,
  password: string,
  fullName: string,
) {
  return apiClient<AuthUser>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
}

export async function loginUser(email: string, password: string) {
  const result = await apiClient<TokenData>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

  if (result.success && result.data) {
    storeTokens(result.data.access_token, result.data.refresh_token);
  }

  return result;
}

export async function forgotPassword(email: string) {
  return apiClient('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(token: string, newPassword: string) {
  return apiClient('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export async function getCurrentUser() {
  return apiClient<AuthUser>('/auth/me');
}

export function logoutUser() {
  clearTokens();
  window.location.href = '/login';
}
