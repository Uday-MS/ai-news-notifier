import { useState, useEffect, useCallback } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { FeedCard } from '@/components/feed/FeedCard';
import { getSaved, type SavedListResponse } from '@/services/savedService';
import type { FeedItem } from '@/services/feedService';

export default function SavedPage() {
  useDocumentTitle('Saved Articles — AI News Notifier');

  const [items, setItems] = useState<FeedItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [hasMore, setHasMore] = useState(false);

  const loadSaved = useCallback(async (offset = 0) => {
    if (offset === 0) setLoading(true);
    setError('');
    try {
      const result = await getSaved(50, offset);
      if (result.success && result.data) {
        const data = result.data as SavedListResponse;
        setItems((prev) => offset === 0 ? data.items : [...prev, ...data.items]);
        setTotal(data.pagination.total);
        setHasMore(data.pagination.has_more);
      }
    } catch {
      setError('Failed to load saved articles.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSaved(0);
  }, [loadSaved]);

  function handleUnsave(id: string) {
    setItems((prev) => prev.filter((item) => item.id !== id));
    setTotal((prev) => Math.max(0, prev - 1));
  }

  function handleLoadMore() {
    loadSaved(items.length);
  }

  return (
    <div className="flex flex-col flex-1">
      {/* Header */}
      <header className="px-4 pt-8 pb-4 border-b border-outline sticky top-0 z-20 bg-surface/95 backdrop-blur-md">
        <div className="max-w-4xl mx-auto w-full">
          <h1 className="text-xl font-bold font-body text-on-surface">Saved Articles</h1>
          <p className="text-sm text-on-surface-variant font-body mt-1">
            {total > 0 ? `${total} article${total !== 1 ? 's' : ''} saved` : 'Your bookmarked articles will appear here'}
          </p>
        </div>
      </header>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-error p-4 bg-error-container/30 mx-8 mt-4 rounded">
          <span className="material-symbols-outlined text-lg">error</span>
          <span className="font-body text-sm">{error}</span>
          <button
            onClick={() => loadSaved(0)}
            className="ml-auto text-sm font-body text-primary hover:underline bg-transparent border-none cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="p-8 max-w-7xl mx-auto w-full">
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="p-6 border border-outline animate-pulse">
                <div className="flex gap-4">
                  <div className="w-10 h-10 rounded-full bg-surface-container" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 bg-surface-container rounded w-1/4" />
                    <div className="h-4 bg-surface-container rounded w-3/4" />
                    <div className="h-3 bg-surface-container rounded w-full" />
                    <div className="h-3 bg-surface-container rounded w-1/2" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && items.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center flex-1 py-20 text-center">
          <span className="material-symbols-outlined text-6xl text-on-surface-variant mb-4">bookmark</span>
          <h3 className="text-xl font-bold text-on-surface mb-2">No Saved Articles</h3>
          <p className="text-on-surface-variant font-body text-sm max-w-sm">
            Bookmark articles from the feed to save them here for later reading. Click the bookmark icon on any article to get started.
          </p>
        </div>
      )}

      {/* Saved articles list */}
      {!loading && items.length > 0 && (
        <div className="max-w-4xl mx-auto w-full">
          <div className="flex flex-col page-transition">
            {items.map((item) => (
              <FeedCard
                key={item.id}
                item={item}
                initialSaved={true}
                onUnsave={handleUnsave}
              />
            ))}
          </div>

          {/* Load more */}
          {hasMore && (
            <button
              onClick={handleLoadMore}
              className="w-full py-4 text-center text-primary font-medium text-sm hover:bg-surface-container transition-colors bg-transparent border-none border-t border-outline cursor-pointer"
            >
              Load more
            </button>
          )}
        </div>
      )}
    </div>
  );
}
