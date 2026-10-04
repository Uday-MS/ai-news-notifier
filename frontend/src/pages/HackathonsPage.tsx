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
  useDocumentTitle('Events — NexusAI');
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
      const searchParams: SearchParams = { sort: 'highest_importance', limit: 20, ...params };
      if (params.category) {
        const result = await searchFeed(searchParams);
        if (result.success && result.data) {
          setItems((prev) => append ? [...prev, ...result.data!.items] : result.data!.items);
          setHasMore(result.data.pagination.has_more);
          setTotalCount(result.data.pagination.total);
        }
      } else {
        const [compResult, hackResult] = await Promise.all([
          searchFeed({ ...searchParams, category: 'competition', limit: 15 }),
          searchFeed({ ...searchParams, category: 'hackathon', limit: 15 }),
        ]);
        const allItems: FeedItem[] = [];
        let total = 0;
        for (const r of [compResult, hackResult]) {
          if (r.success && r.data) { allItems.push(...r.data.items); total += r.data.pagination.total; }
        }
        allItems.sort((a, b) => b.importance_score - a.importance_score);
        setItems(append ? (prev) => [...prev, ...allItems] : allItems);
        setHasMore(total > allItems.length);
        setTotalCount(total);
      }
    } catch { setError('Failed to load events.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    loadEvents(filter === 'all' ? {} : { category: filter });
  }, [filter, loadEvents]);

  return (
    <div className="flex flex-col min-h-screen">
      <div className="sticky top-0 z-10 bg-surface/90 backdrop-blur-md border-b border-outline-variant">
        <div className="px-4 py-2.5 flex items-center justify-between">
          <h2 className="font-headline font-semibold text-[16px] text-on-surface tracking-tight">Hackathons & Competitions</h2>
          {!loading && totalCount > 0 && <span className="badge badge-warning">{totalCount}</span>}
        </div>
        <div className="flex gap-1.5 px-4 pb-2.5 overflow-x-auto no-scrollbar">
          {FILTERS.map((f) => (
            <button key={f.value} onClick={() => setFilter(f.value)}
              className={cn(
                'px-2.5 py-1 text-[11px] rounded border whitespace-nowrap transition-colors cursor-pointer shrink-0 flex items-center gap-1 font-mono uppercase tracking-wider',
                filter === f.value ? 'bg-primary text-[var(--c-accent-text)] border-primary font-medium' : 'bg-transparent text-[var(--c-text-2)] border-[var(--c-border-subtle)] hover:border-[var(--c-border)]'
              )}>
              <span className="material-symbols-outlined text-[12px]">{f.icon}</span>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-[var(--c-danger)] px-4 py-3 bg-[var(--c-danger-dim)] border-b border-outline-variant">
          <span className="material-symbols-outlined text-base">error</span>
          <span className="text-[13px] font-body">{error}</span>
          <button onClick={() => loadEvents(filter === 'all' ? {} : { category: filter })} className="ml-auto text-[12px] font-mono text-primary uppercase tracking-wider hover:underline bg-transparent border-none cursor-pointer">Retry</button>
        </div>
      )}

      {loading && (
        <div className="flex flex-col">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="px-4 py-4 border-b border-outline-variant">
              <div className="flex items-center gap-2 mb-3"><div className="w-7 h-7 rounded bg-[var(--c-elevated)] skeleton-shimmer" /><div className="h-3 bg-[var(--c-elevated)] rounded w-24 skeleton-shimmer" /></div>
              <div className="h-4 bg-[var(--c-elevated)] rounded w-4/5 skeleton-shimmer mb-2" />
              <div className="h-3 bg-[var(--c-elevated)] rounded w-full skeleton-shimmer" />
            </div>
          ))}
        </div>
      )}

      {!loading && items.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-center px-4">
          <div className="w-12 h-12 rounded bg-[var(--c-elevated)] flex items-center justify-center mb-4">
            <span className="material-symbols-outlined text-2xl text-[var(--c-text-3)]">emoji_events</span>
          </div>
          <h3 className="font-headline font-semibold text-[16px] text-on-surface mb-1.5 tracking-tight">No events found</h3>
          <p className="text-[var(--c-text-2)] text-[13px] max-w-xs font-body">
            {filter !== 'all' ? `No ${filter} events yet. Try "All Events".` : 'Events will appear as they are collected from AI sources.'}
          </p>
        </div>
      )}

      <div className="flex flex-col page-transition">
        {!loading && items.map((item) => <FeedCard key={item.id} item={item} showScore score={item.importance_score} />)}
      </div>

      {hasMore && !loading && (
        <button onClick={() => loadEvents({ category: filter === 'all' ? undefined : filter, offset: items.length }, true)}
          className="w-full py-3.5 text-center text-primary font-mono text-[12px] font-medium uppercase tracking-wider hover:bg-[var(--c-elevated)] transition-colors bg-transparent border-none border-t border-outline-variant cursor-pointer">
          Load more →
        </button>
      )}
    </div>
  );
}
