/**
 * Integration service — API calls for pipeline orchestration.
 */

import { apiClient } from './apiClient';

// ── Types ───────────────────────────────────────────────────────────────

export interface SeedResult {
  created: number;
  skipped: number;
  total: number;
  sources: string[];
}

export interface CollectionDetail {
  collector_type: string;
  source_name: string;
  fetched: number;
  emitted: number;
  duplicates: number;
  errors: number;
}

export interface CollectAndProcessResult {
  collection: {
    sources_run: number;
    total_fetched: number;
    total_emitted: number;
    total_duplicates: number;
    errors: number;
    details: CollectionDetail[];
  };
  processing: {
    processed: number;
    failed: number;
    skipped: number;
  };
}

// ── API Calls ───────────────────────────────────────────────────────────

export async function seedSources() {
  return apiClient<SeedResult>('/integration/seed-sources', { method: 'POST' });
}

export async function collectAndProcess() {
  return apiClient<CollectAndProcessResult>('/integration/collect-and-process', {
    method: 'POST',
  });
}
