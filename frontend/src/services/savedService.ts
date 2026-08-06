/**
 * Saved articles service — API calls for bookmarks.
 */

import { apiClient } from './apiClient';
import type { FeedItem, PaginationMeta } from './feedService';

export interface SavedListResponse {
  items: FeedItem[];
  pagination: PaginationMeta;
}

export interface SaveResponse {
  saved_article_id: string;
  event_id: string;
}

export interface SavedCheckResponse {
  is_saved: boolean;
}

export async function saveArticle(eventId: string) {
  return apiClient<SaveResponse>(`/saved/${eventId}`, { method: 'POST' });
}

export async function unsaveArticle(eventId: string) {
  return apiClient<void>(`/saved/${eventId}`, { method: 'DELETE' });
}

export async function getSaved(limit = 50, offset = 0) {
  return apiClient<SavedListResponse>(`/saved?limit=${limit}&offset=${offset}`);
}

export async function checkSaved(eventId: string) {
  return apiClient<SavedCheckResponse>(`/saved/${eventId}/check`);
}
