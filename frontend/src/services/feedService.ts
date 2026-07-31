/**
 * Feed service — API calls for Intelligence Feed & Search.
 */

import { apiClient } from './apiClient';

// ── Types matching backend schemas ──────────────────────────────────────

export interface FeedItem {
  id: string;
  collected_event_id: string;
  cleaned_title: string;
  ai_summary: string;
  ai_category: string;
  ai_tags: string[];
  importance_score: number;
  source: string;
  source_url: string;
  organization: string;
  published_at: string;
  processed_at: string | null;
}

export interface PaginationMeta {
  limit: number;
  offset: number;
  total: number;
  has_more: boolean;
}

export interface FeedSearchResponse {
  items: FeedItem[];
  pagination: PaginationMeta;
}

export interface TagCount {
  tag: string;
  count: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface TrendingResponse {
  top_tags: TagCount[];
  top_categories: CategoryCount[];
  most_important: FeedItem[];
  total_ready: number;
}

export interface FeedDetail extends FeedItem {
  cleaned_summary: string;
  entities: Record<string, unknown>;
  importance_reason: string;
  processing_status: string;
  created_at: string;
}

export interface IntegrationStatus {
  collected_events: number;
  processed_events: number;
  unprocessed_events: number;
  notifications: number;
  delivered_notifications: number;
  pipeline_coverage: number;
}

// ── API Calls ───────────────────────────────────────────────────────────

export interface SearchParams {
  q?: string;
  category?: string;
  source?: string;
  tag?: string;
  importance_min?: number;
  importance_max?: number;
  sort?: string;
  limit?: number;
  offset?: number;
}

export async function getFeed(limit = 50, offset = 0, sort = 'newest') {
  return apiClient<FeedSearchResponse>(`/feed?limit=${limit}&offset=${offset}&sort=${sort}`);
}

export async function searchFeed(params: SearchParams) {
  const query = new URLSearchParams();
  if (params.q) query.set('q', params.q);
  if (params.category) query.set('category', params.category);
  if (params.source) query.set('source', params.source);
  if (params.tag) query.set('tag', params.tag);
  if (params.importance_min !== undefined) query.set('importance_min', String(params.importance_min));
  if (params.importance_max !== undefined) query.set('importance_max', String(params.importance_max));
  if (params.sort) query.set('sort', params.sort);
  query.set('limit', String(params.limit ?? 50));
  query.set('offset', String(params.offset ?? 0));
  return apiClient<FeedSearchResponse>(`/feed/search?${query.toString()}`);
}

export async function getTrending(limit = 10) {
  return apiClient<TrendingResponse>(`/feed/trending?limit=${limit}`);
}

export async function getCategories(limit = 20) {
  return apiClient<CategoryCount[]>(`/feed/categories?limit=${limit}`);
}

export async function getTags(limit = 30) {
  return apiClient<TagCount[]>(`/feed/tags?limit=${limit}`);
}

export async function getFeedDetail(id: string) {
  return apiClient<FeedDetail>(`/feed/${id}`);
}

export async function getIntegrationStatus() {
  return apiClient<IntegrationStatus>('/integration/status');
}
