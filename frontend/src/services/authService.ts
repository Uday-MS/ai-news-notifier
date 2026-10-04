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
  // Sprint 2 — profile fields
  username?: string;
  bio?: string;
  profile_image?: string;
  college?: string;
  degree?: string;
  graduation_year?: number;
  country?: string;
  timezone?: string;
  notification_preference: string;
  onboarding_completed: boolean;
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

// ── Phase 4: OTP Verification ───────────────────────────────────────────

export async function verifyEmailOTP(email: string, otpCode: string) {
  return apiClient<TokenData>('/auth/verify-email/confirm', {
    method: 'POST',
    body: JSON.stringify({ email, otp_code: otpCode }),
  });
}

export async function resendOTP(email: string) {
  return apiClient('/auth/verify-email/resend', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

// ── Phase 4: Google OAuth ───────────────────────────────────────────────

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1';

export function getGoogleLoginUrl(): string {
  return `${API_BASE_URL}/auth/google/login`;
}
