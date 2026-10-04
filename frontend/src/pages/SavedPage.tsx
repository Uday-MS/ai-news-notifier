import { useState, useEffect, useCallback } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { FeedCard } from '@/components/feed/FeedCard';
import { getSaved, type SavedListResponse } from '@/services/savedService';
import type { FeedItem } from '@/services/feedService';

export default function SavedPage() {
  useDocumentTitle('Saved — NexusAI');

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
    } catch { setError('Failed to load saved intelligence.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadSaved(0); }, [loadSaved]);

  function handleUnsave(id: string) {
    setItems((prev) => prev.filter((item) => item.id !== id));
    setTotal((prev) => Math.max(0, prev - 1));
  }

  return (
    <div className="flex flex-col flex-1">
      <header className="px-4 py-3 border-b border-outline-variant sticky top-0 z-20 bg-surface/90 backdrop-blur-md">
        <div className="flex items-center justify-between">
          <h1 className="font-headline font-semibold text-[16px] text-on-surface tracking-tight">Saved</h1>
          {total > 0 && <span className="badge badge-neutral">{total} saved</span>}
        </div>
      </header>

      {error && (
        <div className="flex items-center gap-2 text-[var(--c-danger)] px-4 py-3 bg-[var(--c-danger-dim)] border-b border-outline-variant">
          <span className="material-symbols-outlined text-base">error</span>
          <span className="font-body text-[13px]">{error}</span>
          <button onClick={() => loadSaved(0)} className="ml-auto text-[12px] font-mono text-primary uppercase tracking-wider hover:underline bg-transparent border-none cursor-pointer">Retry</button>
        </div>
      )}

      {loading && (
        <div className="flex flex-col">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="px-4 py-4 border-b border-outline-variant">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-7 h-7 rounded bg-[var(--c-elevated)] skeleton-shimmer" />
                <div className="h-3 bg-[var(--c-elevated)] rounded w-24 skeleton-shimmer" />
              </div>
              <div className="h-4 bg-[var(--c-elevated)] rounded w-4/5 skeleton-shimmer mb-2" />
              <div className="h-3 bg-[var(--c-elevated)] rounded w-full skeleton-shimmer" />
            </div>
          ))}
        </div>
      )}

      {!loading && items.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center flex-1 py-20 text-center px-4">
          <div className="w-12 h-12 rounded bg-[var(--c-elevated)] flex items-center justify-center mb-4">
            <span className="material-symbols-outlined text-2xl text-[var(--c-text-3)]">bookmark</span>
          </div>
          <h3 className="font-headline font-semibold text-[16px] text-on-surface mb-1.5 tracking-tight">No saved intelligence</h3>
          <p className="text-[var(--c-text-2)] font-body text-[13px] max-w-xs leading-relaxed">
            Bookmark articles from the feed to save them here. Click the bookmark icon on any intelligence card.
          </p>
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="flex flex-col page-transition">
          {items.map((item) => (
            <FeedCard key={item.id} item={item} initialSaved={true} onUnsave={handleUnsave} />
          ))}
          {hasMore && (
            <button onClick={() => loadSaved(items.length)}
              className="w-full py-3.5 text-center text-primary font-mono text-[12px] font-medium uppercase tracking-wider hover:bg-[var(--c-elevated)] transition-colors bg-transparent border-none border-t border-outline-variant cursor-pointer">
              Load more →
            </button>
          )}
        </div>
      )}
    </div>
  );
}
