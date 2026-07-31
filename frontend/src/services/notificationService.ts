/**
 * Notification service — API calls for notification management.
 */

import { apiClient } from './apiClient';
import type { PaginationMeta } from './feedService';

// ── Types matching backend schemas ──────────────────────────────────────

export interface NotificationItem {
  id: string;
  notification_type: string;
  channel: string;
  title: string;
  message: string;
  status: string;
  recommendation_score: number;
  created_at: string;
  read_at: string | null;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  pagination: PaginationMeta;
}

export interface UnreadResponse {
  items: NotificationItem[];
  pagination: PaginationMeta;
}

export interface NotificationGenerateResponse {
  generated: number;
  skipped_duplicate: number;
  skipped_cooldown: number;
  skipped_low_score: number;
}

export interface NotificationStatusResponse {
  notification_id: string | null;
  status: string;
  updated_count: number;
}

// ── API Calls ───────────────────────────────────────────────────────────

export async function getNotifications(
  status?: string,
  limit = 50,
  offset = 0,
) {
  const query = new URLSearchParams();
  if (status) query.set('status', status);
  query.set('limit', String(limit));
  query.set('offset', String(offset));
  return apiClient<NotificationListResponse>(`/notifications?${query.toString()}`);
}

export async function getUnread(limit = 50, offset = 0) {
  return apiClient<UnreadResponse>(
    `/notifications/unread?limit=${limit}&offset=${offset}`,
  );
}

export async function generateNotifications(
  minScore = 30,
  maxCount = 10,
) {
  return apiClient<NotificationGenerateResponse>('/notifications/generate', {
    method: 'POST',
    body: JSON.stringify({ min_score: minScore, max_count: maxCount }),
  });
}

export async function markRead(id: string) {
  return apiClient<NotificationStatusResponse>(`/notifications/${id}/read`, {
    method: 'PATCH',
  });
}

export async function markAllRead() {
  return apiClient<NotificationStatusResponse>('/notifications/read-all', {
    method: 'PATCH',
  });
}

export async function deleteNotification(id: string) {
  return apiClient<NotificationStatusResponse>(`/notifications/${id}`, {
    method: 'DELETE',
  });
}
