/**
 * HomePage — Intelligence feed with For You / Latest tabs.
 */

import { useState, useEffect, useCallback } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { FeedCard } from '@/components/feed/FeedCard';
import { getForYou, type RecommendationItem } from '@/services/recommendationService';
import { getFeed, type FeedItem } from '@/services/feedService';
import { cn } from '@/utils/cn';

type Tab = 'for-you' | 'latest';

export default function HomePage() {
  useDocumentTitle('Home — NexusAI');

  const [activeTab, setActiveTab] = useState<Tab>('for-you');
  const [forYouItems, setForYouItems] = useState<RecommendationItem[]>([]);
  const [latestItems, setLatestItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [hasMore, setHasMore] = useState(false);

  const loadForYou = useCallback(async (offset = 0) => {
    setLoading(true);
    setError('');
    try {
      const result = await getForYou(20, offset);
      if (result.success && result.data) {
        setForYouItems((prev) => offset === 0 ? result.data!.items : [...prev, ...result.data!.items]);
        setHasMore(result.data.pagination.has_more);
      }
    } catch {
      setError('Failed to load recommendations.');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadLatest = useCallback(async (offset = 0) => {
    setLoading(true);
    setError('');
    try {
      const result = await getFeed(20, offset, 'newest');
      if (result.success && result.data) {
        setLatestItems((prev) => offset === 0 ? result.data!.items : [...prev, ...result.data!.items]);
        setHasMore(result.data.pagination.has_more);
      }
    } catch {
      setError('Failed to load feed.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'for-you') loadForYou(0);
    else loadLatest(0);
  }, [activeTab, loadForYou, loadLatest]);

  function handleLoadMore() {
    const offset = activeTab === 'for-you' ? forYouItems.length : latestItems.length;
    if (activeTab === 'for-you') loadForYou(offset);
    else loadLatest(offset);
  }

  const items = activeTab === 'for-you' ? forYouItems : latestItems;

  return (
    <div className="flex flex-col min-h-screen">
      {/* Tab Header */}
      <div className="sticky top-0 z-10 bg-surface/90 backdrop-blur-md border-b border-outline-variant">
        <div className="flex">
          {(['for-you', 'latest'] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'flex-1 py-3 text-center text-[13px] font-body font-medium hover:bg-[var(--c-elevated)] transition-colors bg-transparent border-none cursor-pointer relative tracking-tight',
                activeTab === tab ? 'text-on-surface' : 'text-on-surface-variant'
              )}
            >
              {tab === 'for-you' ? 'For You' : 'Latest'}
              {activeTab === tab && (
                <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-10 h-[2px] bg-primary rounded-full" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-[var(--c-danger)] px-4 py-3 bg-[var(--c-danger-dim)] border-b border-outline-variant">
          <span className="material-symbols-outlined text-base">error</span>
          <span className="font-body text-[13px]">{error}</span>
          <button
            onClick={() => activeTab === 'for-you' ? loadForYou(0) : loadLatest(0)}
            className="ml-auto text-[12px] font-mono text-primary uppercase tracking-wider hover:underline bg-transparent border-none cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && items.length === 0 && (
        <div className="flex flex-col">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="px-4 py-4 border-b border-outline-variant">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-7 h-7 rounded bg-[var(--c-elevated)] skeleton-shimmer" />
                <div className="h-3 bg-[var(--c-elevated)] rounded w-24 skeleton-shimmer" />
                <div className="h-3 bg-[var(--c-elevated)] rounded w-8 ml-auto skeleton-shimmer" />
              </div>
              <div className="h-4 bg-[var(--c-elevated)] rounded w-4/5 skeleton-shimmer mb-2" />
              <div className="h-3 bg-[var(--c-elevated)] rounded w-full skeleton-shimmer mb-1" />
              <div className="h-3 bg-[var(--c-elevated)] rounded w-2/3 skeleton-shimmer" />
              <div className="flex gap-1 mt-3">
                <div className="h-5 w-12 bg-[var(--c-elevated)] rounded skeleton-shimmer" />
                <div className="h-5 w-16 bg-[var(--c-elevated)] rounded skeleton-shimmer" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && items.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-center px-4">
          <div className="w-12 h-12 rounded bg-[var(--c-elevated)] flex items-center justify-center mb-4">
            <span className="material-symbols-outlined text-2xl text-[var(--c-text-3)]">
              {activeTab === 'for-you' ? 'auto_awesome' : 'newspaper'}
            </span>
          </div>
          <h3 className="font-headline font-semibold text-[16px] text-on-surface mb-1.5 tracking-tight">
            {activeTab === 'for-you' ? 'No recommendations yet' : 'No intelligence yet'}
          </h3>
          <p className="text-[var(--c-text-2)] font-body text-[13px] max-w-xs leading-relaxed">
            {activeTab === 'for-you'
              ? 'Your personalized feed will populate as intelligence is collected and processed.'
              : 'Intelligence articles will appear here once the collectors run.'}
          </p>
        </div>
      )}

      {/* Feed */}
      <div className="flex flex-col page-transition">
        {items.map((item) => (
          <FeedCard
            key={item.id}
            item={item}
            showScore={activeTab === 'for-you'}
            score={activeTab === 'for-you' ? (item as RecommendationItem).recommendation_score : undefined}
            reasons={activeTab === 'for-you' ? (item as RecommendationItem).recommendation_reasons : undefined}
            whyItMatters={activeTab === 'for-you' ? (item as RecommendationItem).why_it_matters : undefined}
          />
        ))}
      </div>

      {/* Load more */}
      {hasMore && !loading && (
        <button
          onClick={handleLoadMore}
          className="w-full py-3.5 text-center text-primary font-mono text-[12px] font-medium uppercase tracking-wider hover:bg-[var(--c-elevated)] transition-colors bg-transparent border-none border-t border-outline-variant cursor-pointer"
        >
          Load more intelligence →
        </button>
      )}

      {/* Loading more indicator */}
      {loading && items.length > 0 && (
        <div className="flex justify-center py-4">
          <span className="material-symbols-outlined text-primary animate-spin">progress_activity</span>
        </div>
      )}
    </div>
  );
}
