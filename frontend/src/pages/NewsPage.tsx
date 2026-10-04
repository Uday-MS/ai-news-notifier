import { useState, useEffect, useCallback } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useSearchParams } from 'react-router-dom';
import { FeedCard } from '@/components/feed/FeedCard';
import { searchFeed, getTrending, getCategories, type FeedItem, type TrendingResponse, type CategoryCount, type SearchParams } from '@/services/feedService';
import { cn } from '@/utils/cn';

export default function NewsPage() {
  useDocumentTitle('Explore — NexusAI');
  const [urlParams] = useSearchParams();
  const [items, setItems] = useState<FeedItem[]>([]);
  const [trending, setTrending] = useState<TrendingResponse | null>(null);
  const [categories, setCategories] = useState<CategoryCount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState(urlParams.get('q') ?? '');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);

  const loadFeed = useCallback(async (params: SearchParams = {}, append = false) => {
    if (!append) setLoading(true);
    setError('');
    try {
      const result = await searchFeed({ sort: 'highest_importance', limit: 20, ...params });
      if (result.success && result.data) {
        setItems((prev) => append ? [...prev, ...result.data!.items] : result.data!.items);
        setHasMore(result.data.pagination.has_more);
      }
    } catch { setError('Failed to load intelligence.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const q = urlParams.get('q') ?? '';
    const tag = urlParams.get('tag') ?? '';
    const cat = urlParams.get('category') ?? '';
    setSearchQuery(q);
    if (cat) setActiveCategory(cat);
    loadFeed({ q: q || undefined, tag: tag || undefined, category: cat || undefined });
    getTrending(10).then((r) => r.success && r.data && setTrending(r.data));
    getCategories(20).then((r) => r.success && r.data && setCategories(r.data));
  }, [loadFeed, urlParams]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    loadFeed({ q: searchQuery || undefined, category: activeCategory ?? undefined });
  }

  function handleCategoryFilter(cat: string | null) {
    setActiveCategory(cat);
    loadFeed({ q: searchQuery || undefined, category: cat ?? undefined });
  }

  return (
    <div className="flex flex-col min-h-screen">
      <div className="sticky top-0 z-10 bg-surface/90 backdrop-blur-md border-b border-outline-variant">
        <div className="px-4 py-2.5 flex items-center justify-between">
          <h2 className="font-headline font-semibold text-[16px] text-on-surface tracking-tight">Explore</h2>
          {trending && !loading && (
            <span className="badge badge-neutral">
              {trending.total_ready} articles
            </span>
          )}
        </div>
        <form onSubmit={handleSearch} className="px-4 pb-2.5">
          <div className="relative">
            <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--c-text-3)] text-base">search</span>
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search intelligence..."
              className="w-full py-2 pl-9 pr-3 bg-[var(--c-elevated)] border border-[var(--c-border-subtle)] rounded text-[13px] text-on-surface placeholder:text-[var(--c-text-3)] focus:outline-none focus:border-primary transition-colors font-body" />
          </div>
        </form>
        {categories.length > 0 && (
          <div className="flex gap-1.5 px-4 pb-2.5 overflow-x-auto no-scrollbar">
            <button onClick={() => handleCategoryFilter(null)}
              className={cn('px-2.5 py-1 text-[11px] rounded border whitespace-nowrap transition-colors cursor-pointer shrink-0 font-mono uppercase tracking-wider',
                !activeCategory ? 'bg-primary text-[var(--c-accent-text)] border-primary font-medium' : 'bg-transparent text-[var(--c-text-2)] border-[var(--c-border-subtle)] hover:border-[var(--c-border)]')}>All</button>
            {categories.map((cat) => (
              <button key={cat.category} onClick={() => handleCategoryFilter(cat.category)}
                className={cn('px-2.5 py-1 text-[11px] rounded border whitespace-nowrap transition-colors cursor-pointer shrink-0 font-mono uppercase tracking-wider',
                  activeCategory === cat.category ? 'bg-primary text-[var(--c-accent-text)] border-primary font-medium' : 'bg-transparent text-[var(--c-text-2)] border-[var(--c-border-subtle)] hover:border-[var(--c-border)]')}>
                {cat.category.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-[var(--c-danger)] px-4 py-3 bg-[var(--c-danger-dim)] border-b border-outline-variant">
          <span className="material-symbols-outlined text-base">error</span>
          <span className="text-[13px] font-body">{error}</span>
          <button onClick={() => loadFeed()} className="ml-auto text-[12px] font-mono text-primary uppercase tracking-wider hover:underline bg-transparent border-none cursor-pointer">Retry</button>
        </div>
      )}

      {loading && (
        <div className="flex flex-col">
          {[1, 2, 3, 4, 5].map((i) => (
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
        <div className="flex flex-col items-center justify-center py-20 text-center px-4">
          <div className="w-12 h-12 rounded bg-[var(--c-elevated)] flex items-center justify-center mb-4">
            <span className="material-symbols-outlined text-2xl text-[var(--c-text-3)]">search_off</span>
          </div>
          <h3 className="font-headline font-semibold text-[16px] text-on-surface mb-1.5 tracking-tight">No intelligence found</h3>
          <p className="text-[var(--c-text-2)] text-[13px] max-w-xs font-body">{searchQuery ? 'Try a different search query.' : 'Intelligence will appear once collectors run.'}</p>
        </div>
      )}

      <div className="flex flex-col page-transition">
        {!loading && items.map((item) => <FeedCard key={item.id} item={item} showScore score={item.importance_score} />)}
      </div>

      {hasMore && !loading && (
        <button onClick={() => loadFeed({ q: searchQuery || undefined, category: activeCategory ?? undefined, offset: items.length }, true)}
          className="w-full py-3.5 text-center text-primary font-mono text-[12px] font-medium uppercase tracking-wider hover:bg-[var(--c-elevated)] transition-colors bg-transparent border-none border-t border-outline-variant cursor-pointer">
          Load more →
        </button>
      )}
    </div>
  );
}
