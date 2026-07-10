/**
 * User service — API calls for profile, interests, and preferences.
 */

import { apiClient } from './apiClient';
import type { AuthUser } from './authService';

// ── Types ───────────────────────────────────────────────────────────────

export interface ProfileUpdate {
  full_name?: string;
  username?: string;
  bio?: string;
  profile_image?: string;
  college?: string;
  degree?: string;
  graduation_year?: number;
  country?: string;
  timezone?: string;
  notification_preference?: string;
  onboarding_completed?: boolean;
}

export interface InterestsData {
  interests: string[];
}

export interface PreferencesData {
  opportunity_preferences: string[];
  notification_preference?: string;
}

// ── API Calls ───────────────────────────────────────────────────────────

export async function getProfile() {
  return apiClient<AuthUser>('/users/me');
}

export async function updateProfile(data: ProfileUpdate) {
  return apiClient<AuthUser>('/users/me', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function getInterests() {
  return apiClient<InterestsData>('/users/interests');
}

export async function updateInterests(interests: string[]) {
  return apiClient<InterestsData>('/users/interests', {
    method: 'PUT',
    body: JSON.stringify({ interests }),
  });
}

export async function getPreferences() {
  return apiClient<PreferencesData>('/users/preferences');
}

export async function updatePreferences(opportunityPreferences: string[]) {
  return apiClient<{ opportunity_preferences: string[] }>('/users/preferences', {
    method: 'PUT',
    body: JSON.stringify({ opportunity_preferences: opportunityPreferences }),
  });
}
