import { useState, useEffect, useCallback } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { FeedCard } from '@/components/feed/FeedCard';
import { getForYou, type RecommendationItem } from '@/services/recommendationService';
import { getFeed, type FeedItem } from '@/services/feedService';
import { cn } from '@/utils/cn';

type Tab = 'for-you' | 'latest';

export default function HomePage() {
  useDocumentTitle('Home — AI News Notifier');

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
    if (activeTab === 'for-you') {
      loadForYou(0);
    } else {
      loadLatest(0);
    }
  }, [activeTab, loadForYou, loadLatest]);

  function handleLoadMore() {
    const offset = activeTab === 'for-you' ? forYouItems.length : latestItems.length;
    if (activeTab === 'for-you') loadForYou(offset);
    else loadLatest(offset);
  }

  const items = activeTab === 'for-you' ? forYouItems : latestItems;

  return (
    <div className="flex flex-col min-h-screen">
      {/* Sticky Tab Header */}
      <div className="sticky top-0 z-10 bg-surface/95 backdrop-blur-md border-b border-outline">
        <div className="flex">
          <button
            onClick={() => setActiveTab('for-you')}
            className={cn(
              'flex-1 py-3.5 text-center text-[15px] font-body font-bold hover:bg-surface-container transition-colors bg-transparent border-none cursor-pointer relative',
              activeTab === 'for-you' ? 'text-on-surface' : 'text-on-surface-variant'
            )}
          >
            For You
            {activeTab === 'for-you' && (
              <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-14 h-1 bg-primary rounded-full" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('latest')}
            className={cn(
              'flex-1 py-3.5 text-center text-[15px] font-body hover:bg-surface-container transition-colors bg-transparent border-none cursor-pointer relative',
              activeTab === 'latest' ? 'text-on-surface font-bold' : 'text-on-surface-variant'
            )}
          >
            Latest
            {activeTab === 'latest' && (
              <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-14 h-1 bg-primary rounded-full" />
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-error p-4 bg-error-container/30">
          <span className="material-symbols-outlined text-lg">error</span>
          <span className="font-body text-sm">{error}</span>
          <button
            onClick={() => activeTab === 'for-you' ? loadForYou(0) : loadLatest(0)}
            className="ml-auto text-sm font-body text-primary hover:underline bg-transparent border-none cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && items.length === 0 && (
        <div className="flex flex-col">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="px-4 py-4 border-b border-outline animate-pulse">
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-full bg-surface-container" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 bg-surface-container rounded w-1/3" />
                  <div className="h-4 bg-surface-container rounded w-3/4" />
                  <div className="h-3 bg-surface-container rounded w-full" />
                  <div className="h-3 bg-surface-container rounded w-2/3" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && items.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="material-symbols-outlined text-5xl text-on-surface-variant mb-4">
            {activeTab === 'for-you' ? 'auto_awesome' : 'newspaper'}
          </span>
          <h3 className="text-lg font-bold text-on-surface mb-2">
            {activeTab === 'for-you' ? 'No recommendations yet' : 'No news yet'}
          </h3>
          <p className="text-on-surface-variant font-body text-sm max-w-xs">
            {activeTab === 'for-you'
              ? 'Your personalized feed will populate as AI news is collected and processed.'
              : 'News articles will appear here once the collectors run.'}
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
          />
        ))}
      </div>

      {/* Load more */}
      {hasMore && !loading && (
        <button
          onClick={handleLoadMore}
          className="w-full py-4 text-center text-primary font-body font-bold text-sm hover:bg-surface-container transition-colors bg-transparent border-none border-t border-outline cursor-pointer"
        >
          Load more
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
