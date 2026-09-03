import { useState, useEffect, useCallback } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { FeedCard } from '@/components/feed/FeedCard';
import { searchFeed, type FeedItem, type SearchParams } from '@/services/feedService';
import { cn } from '@/utils/cn';

type Filter = 'all' | 'competition' | 'hackathon';

const FILTERS: { value: Filter; label: string; icon: string }[] = [
  { value: 'all', label: 'All Events', icon: 'emoji_events' },
  { value: 'competition', label: 'Competitions', icon: 'trophy' },
  { value: 'hackathon', label: 'Hackathons', icon: 'code' },
];

export default function HackathonsPage() {
  useDocumentTitle('Hackathons & Competitions — AI News Notifier');
  const [filter, setFilter] = useState<Filter>('all');
  const [items, setItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [hasMore, setHasMore] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  const loadEvents = useCallback(async (params: SearchParams = {}, append = false) => {
    if (!append) setLoading(true);
    setError('');
    try {
      const searchParams: SearchParams = {
        sort: 'highest_importance',
        limit: 20,
        ...params,
      };

      if (params.category) {
        const result = await searchFeed(searchParams);
        if (result.success && result.data) {
          setItems((prev) => append ? [...prev, ...result.data!.items] : result.data!.items);
          setHasMore(result.data.pagination.has_more);
          setTotalCount(result.data.pagination.total);
        }
      } else {
        // "All" — load from both competition and hackathon categories
        const [compResult, hackResult] = await Promise.all([
          searchFeed({ ...searchParams, category: 'competition', limit: 15 }),
          searchFeed({ ...searchParams, category: 'hackathon', limit: 15 }),
        ]);
        const allItems: FeedItem[] = [];
        let total = 0;
        for (const r of [compResult, hackResult]) {
          if (r.success && r.data) {
            allItems.push(...r.data.items);
            total += r.data.pagination.total;
          }
        }
        allItems.sort((a, b) => b.importance_score - a.importance_score);
        setItems(append ? (prev) => [...prev, ...allItems] : allItems);
        setHasMore(total > allItems.length);
        setTotalCount(total);
      }
    } catch {
      setError('Failed to load events.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEvents(filter === 'all' ? {} : { category: filter });
  }, [filter, loadEvents]);

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-surface/95 backdrop-blur-md border-b border-outline">
        <div className="px-4 py-2.5">
          <h2 className="text-xl font-bold text-on-surface">Hackathons & Competitions</h2>
          <p className="text-[13px] text-on-surface-variant mt-0.5">AI competitions, challenges, and hackathon events</p>
        </div>

        {/* Filters */}
        <div className="flex gap-2 px-4 pb-3 overflow-x-auto no-scrollbar">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={cn(
                'px-3 py-1.5 text-[13px] rounded-full border whitespace-nowrap transition-colors cursor-pointer shrink-0 flex items-center gap-1.5',
                filter === f.value
                  ? 'bg-on-surface text-surface border-on-surface font-semibold'
                  : 'bg-transparent text-on-surface border-[var(--c-border-strong)] hover:bg-[var(--c-elevated)]'
              )}
            >
              <span className="material-symbols-outlined text-[14px]">{f.icon}</span>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      {!loading && items.length > 0 && (
        <div className="px-4 py-2 border-b border-outline text-[13px] text-on-surface-variant flex items-center gap-1.5">
          <span className="material-symbols-outlined text-sm">emoji_events</span>
          {totalCount} event{totalCount !== 1 ? 's' : ''} found
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-error px-4 py-3 bg-error-container/30">
          <span className="material-symbols-outlined text-lg">error</span>
          <span className="text-sm">{error}</span>
          <button onClick={() => loadEvents(filter === 'all' ? {} : { category: filter })} className="ml-auto text-sm text-primary hover:underline bg-transparent border-none cursor-pointer">Retry</button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex flex-col">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="px-4 py-3 border-b border-outline animate-pulse">
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-full bg-[var(--c-elevated)]" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 bg-[var(--c-elevated)] rounded w-1/4" />
                  <div className="h-4 bg-[var(--c-elevated)] rounded w-3/4" />
                  <div className="h-3 bg-[var(--c-elevated)] rounded w-full" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty */}
      {!loading && items.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="material-symbols-outlined text-5xl text-on-surface-variant mb-4">emoji_events</span>
          <h3 className="text-lg font-bold text-on-surface mb-2">No events found</h3>
          <p className="text-on-surface-variant text-sm max-w-xs">
            {filter !== 'all'
              ? `No ${filter} events yet. Try "All Events".`
              : 'Hackathons and competitions will appear as they are collected from AI sources.'}
          </p>
        </div>
      )}

      {/* Feed */}
      <div className="flex flex-col page-transition">
        {!loading && items.map((item) => (
          <FeedCard key={item.id} item={item} showScore score={item.importance_score} />
        ))}
      </div>

      {/* Load more */}
      {hasMore && !loading && (
        <button
          onClick={() => loadEvents(
            { category: filter === 'all' ? undefined : filter, offset: items.length },
            true
          )}
          className="w-full py-4 text-center text-primary font-semibold text-[15px] hover:bg-[var(--c-raised)] transition-colors bg-transparent border-none border-t border-outline cursor-pointer"
        >
          Show more
        </button>
      )}
    </div>
  );
}
