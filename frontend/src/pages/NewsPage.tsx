import { useState, useEffect, useCallback } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useSearchParams } from 'react-router-dom';
import { FeedCard } from '@/components/feed/FeedCard';
import { searchFeed, getTrending, getCategories, type FeedItem, type TrendingResponse, type CategoryCount, type SearchParams } from '@/services/feedService';
import { cn } from '@/utils/cn';

export default function NewsPage() {
  useDocumentTitle('Explore — AI News Notifier');
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
    } catch { setError('Failed to load news.'); }
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
      <div className="sticky top-0 z-10 bg-surface/95 backdrop-blur-md border-b border-outline">
        <div className="px-4 py-2.5">
          <h2 className="text-xl font-bold text-on-surface">Explore</h2>
        </div>
        <form onSubmit={handleSearch} className="px-4 pb-3">
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg">search</span>
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search AI news"
              className="w-full py-2.5 pl-10 pr-4 bg-[var(--c-elevated)] border-none rounded-full text-[15px] text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary focus:bg-surface transition-all" />
          </div>
        </form>
        {categories.length > 0 && (
          <div className="flex gap-2 px-4 pb-3 overflow-x-auto no-scrollbar">
            <button onClick={() => handleCategoryFilter(null)}
              className={cn('px-3 py-1.5 text-[13px] rounded-full border whitespace-nowrap transition-colors cursor-pointer shrink-0',
                !activeCategory ? 'bg-on-surface text-surface border-on-surface font-semibold' : 'bg-transparent text-on-surface border-[var(--c-border-strong)] hover:bg-[var(--c-elevated)]')}>All</button>
            {categories.map((cat) => (
              <button key={cat.category} onClick={() => handleCategoryFilter(cat.category)}
                className={cn('px-3 py-1.5 text-[13px] rounded-full border whitespace-nowrap transition-colors cursor-pointer shrink-0',
                  activeCategory === cat.category ? 'bg-on-surface text-surface border-on-surface font-semibold' : 'bg-transparent text-on-surface border-[var(--c-border-strong)] hover:bg-[var(--c-elevated)]')}>
                {cat.category.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        )}
      </div>

      {trending && !loading && items.length > 0 && (
        <div className="px-4 py-2 border-b border-outline text-[13px] text-on-surface-variant flex items-center gap-1.5">
          <span className="material-symbols-outlined text-sm">trending_up</span>
          {trending.total_ready} articles available
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-error px-4 py-3 bg-error-container/30">
          <span className="material-symbols-outlined text-lg">error</span>
          <span className="text-sm">{error}</span>
          <button onClick={() => loadFeed()} className="ml-auto text-sm text-primary hover:underline bg-transparent border-none cursor-pointer">Retry</button>
        </div>
      )}

      {loading && (
        <div className="flex flex-col">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="px-4 py-3 border-b border-outline animate-pulse">
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-full bg-[var(--c-elevated)]" />
                <div className="flex-1 space-y-2"><div className="h-3 bg-[var(--c-elevated)] rounded w-1/4" /><div className="h-4 bg-[var(--c-elevated)] rounded w-3/4" /><div className="h-3 bg-[var(--c-elevated)] rounded w-full" /></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && items.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="material-symbols-outlined text-5xl text-on-surface-variant mb-4">search_off</span>
          <h3 className="text-lg font-bold text-on-surface mb-2">No articles found</h3>
          <p className="text-on-surface-variant text-sm max-w-xs">{searchQuery ? 'Try a different search term.' : 'Articles will appear once collectors run.'}</p>
        </div>
      )}

      <div className="flex flex-col page-transition">
        {!loading && items.map((item) => <FeedCard key={item.id} item={item} showScore score={item.importance_score} />)}
      </div>

      {hasMore && !loading && (
        <button onClick={() => loadFeed({ q: searchQuery || undefined, category: activeCategory ?? undefined, offset: items.length }, true)}
          className="w-full py-4 text-center text-primary font-semibold text-[15px] hover:bg-[var(--c-raised)] transition-colors bg-transparent border-none border-t border-outline cursor-pointer">Show more</button>
      )}
    </div>
  );
}
