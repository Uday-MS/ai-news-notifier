/**
 * Recommendation service — API calls for personalized feed & preferences.
 */

import { apiClient } from './apiClient';
import type { FeedItem, PaginationMeta } from './feedService';

// ── Types matching backend schemas ──────────────────────────────────────

export interface RecommendationItem extends FeedItem {
  recommendation_score: number;
  recommendation_reasons: string[];
}

export interface PersonalizedFeedResponse {
  items: RecommendationItem[];
  pagination: PaginationMeta;
}

export interface ScoreFactor {
  factor: string;
  score: number;
  reason: string;
}

export interface RecommendationExplanation {
  event_id: string;
  cleaned_title: string;
  total_score: number;
  factors: ScoreFactor[];
}

export interface RecommendationPreferences {
  user_id: string;
  preferred_categories: string[];
  preferred_sources: string[];
  muted_categories: string[];
  muted_sources: string[];
}

export interface RecommendationPreferencesInput {
  preferred_categories?: string[];
  preferred_sources?: string[];
  muted_categories?: string[];
  muted_sources?: string[];
}

// ── API Calls ───────────────────────────────────────────────────────────

export async function getRecommendations(limit = 20, offset = 0) {
  return apiClient<PersonalizedFeedResponse>(
    `/recommendations?limit=${limit}&offset=${offset}`,
  );
}

export async function getForYou(limit = 20, offset = 0) {
  return apiClient<PersonalizedFeedResponse>(
    `/recommendations/for-you?limit=${limit}&offset=${offset}`,
  );
}

export async function getRecommendationTrending(limit = 20) {
  return apiClient<PersonalizedFeedResponse>(
    `/recommendations/trending?limit=${limit}`,
  );
}

export async function explainRecommendation(eventId: string) {
  return apiClient<RecommendationExplanation>(
    `/recommendations/explain/${eventId}`,
  );
}

export async function getRecommendationPreferences() {
  return apiClient<RecommendationPreferences>('/recommendations/preferences');
}

export async function setRecommendationPreferences(prefs: RecommendationPreferencesInput) {
  return apiClient<RecommendationPreferences>('/recommendations/preferences', {
    method: 'POST',
    body: JSON.stringify(prefs),
  });
}
