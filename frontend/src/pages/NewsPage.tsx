import { useState, useEffect, useCallback } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { FeedCard } from '@/components/feed/FeedCard';
import {
  searchFeed,
  getTrending,
  getCategories,
  getIntegrationStatus,
  type FeedItem,
  type TrendingResponse,
  type CategoryCount,
  type IntegrationStatus,
  type SearchParams,
} from '@/services/feedService';

export default function NewsPage() {
  useDocumentTitle('AI News — Intelligence Feed');

  const [items, setItems] = useState<FeedItem[]>([]);
  const [trending, setTrending] = useState<TrendingResponse | null>(null);
  const [categories, setCategories] = useState<CategoryCount[]>([]);
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);

  const loadFeed = useCallback(async (params: SearchParams = {}, append = false) => {
    if (!append) setLoading(true);
    setError('');
    try {
      const result = await searchFeed({
        sort: 'highest_importance',
        limit: 20,
        ...params,
      });
      if (result.success && result.data) {
        setItems((prev) => append ? [...prev, ...result.data!.items] : result.data!.items);
        setHasMore(result.data.pagination.has_more);
      }
    } catch {
      setError('Failed to load news.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFeed();
    getTrending(10).then((r) => r.success && r.data && setTrending(r.data));
    getCategories(20).then((r) => r.success && r.data && setCategories(r.data));
    getIntegrationStatus().then((r) => r.success && r.data && setStatus(r.data));
  }, [loadFeed]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    loadFeed({ q: searchQuery || undefined, category: activeCategory ?? undefined });
  }

  function handleCategoryFilter(cat: string | null) {
    setActiveCategory(cat);
    loadFeed({ q: searchQuery || undefined, category: cat ?? undefined });
  }

  function handleLoadMore() {
    loadFeed(
      { q: searchQuery || undefined, category: activeCategory ?? undefined, offset: items.length },
      true,
    );
  }

  const heroItem = trending?.most_important?.[0];
  const secondaryItems = trending?.most_important?.slice(1, 3) ?? [];

  return (
    <div className="p-8 max-w-[1600px] mx-auto w-full">
      {/* Newspaper Header */}
      <div className="text-center mb-10 py-6 border-y-4 border-primary">
        <h2 className="font-headline text-[5rem] leading-none uppercase tracking-tighter text-primary">
          Intelligence Feed
        </h2>
        <div className="flex justify-between items-center mt-4 px-4 font-label text-label-md text-on-surface-variant uppercase tracking-widest border-t border-outline-variant pt-2">
          <span>{trending ? `${trending.total_ready} Articles` : 'Loading...'}</span>
          <span>Global Operations</span>
          <span>Updated: Just Now</span>
        </div>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="mb-6 flex gap-3">
        <div className="flex-1 relative">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-xl">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search AI news..."
            className="input-field pl-10 w-full"
          />
        </div>
        <button
          type="submit"
          className="px-6 py-2 bg-primary text-on-primary font-label uppercase tracking-wider text-sm hover:opacity-90 transition-opacity border-none cursor-pointer"
        >
          Search
        </button>
      </form>

      {/* Category Filters */}
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-8">
          <button
            onClick={() => handleCategoryFilter(null)}
            className={`px-3 py-1.5 text-xs font-label uppercase tracking-wider border transition-colors cursor-pointer ${
              !activeCategory
                ? 'bg-primary text-on-primary border-primary'
                : 'bg-transparent text-on-surface-variant border-outline hover:border-primary'
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat.category}
              onClick={() => handleCategoryFilter(cat.category)}
              className={`px-3 py-1.5 text-xs font-label uppercase tracking-wider border transition-colors cursor-pointer ${
                activeCategory === cat.category
                  ? 'bg-primary text-on-primary border-primary'
                  : 'bg-transparent text-on-surface-variant border-outline hover:border-primary'
              }`}
            >
              {cat.category.replace(/_/g, ' ')} ({cat.count})
            </button>
          ))}
        </div>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Center Content */}
        <div className="lg:col-span-8 flex flex-col gap-8">
          {/* Hero Article */}
          {heroItem && !loading && (
            <article className="border border-primary bg-surface p-8">
              <span className="font-label text-label-md uppercase tracking-widest text-secondary mb-4 block">
                {heroItem.ai_category.replace(/_/g, ' ')}
              </span>
              <h3 className="font-headline text-headline-lg text-primary mb-4">
                <a
                  href={heroItem.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="no-underline text-inherit hover:underline decoration-2 underline-offset-4"
                >
                  {heroItem.cleaned_title}
                </a>
              </h3>
              <p className="font-body text-body-lg text-on-surface-variant mb-6 leading-relaxed">
                {heroItem.ai_summary}
              </p>
              <div className="flex items-center gap-3 pt-4 border-t border-outline-variant flex-wrap">
                {heroItem.ai_tags.slice(0, 4).map((tag) => (
                  <span key={tag} className="text-xs font-label text-primary bg-primary-container px-2 py-0.5 rounded-full">
                    {tag}
                  </span>
                ))}
                <span className="ml-auto font-label text-sm text-secondary">
                  Score: {heroItem.importance_score}
                </span>
              </div>
            </article>
          )}

          {/* Secondary featured articles */}
          {secondaryItems.length > 0 && !loading && (
            <>
              <div className="border-t-4 border-primary my-0" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {secondaryItems.map((item) => (
                  <article key={item.id} className="group cursor-pointer">
                    <div className="w-full h-48 border border-primary mb-4 bg-surface-container flex flex-col justify-center items-center p-6 text-center">
                      <span className="material-symbols-outlined text-[48px] text-primary mb-3">
                        {item.ai_category === 'research' ? 'biotech' : item.ai_category === 'ai_model' ? 'smart_toy' : 'article'}
                      </span>
                      <h4 className="font-headline text-headline-sm text-primary leading-tight">
                        {item.cleaned_title}
                      </h4>
                    </div>
                    <span className="font-label text-label-md uppercase tracking-widest text-secondary mb-2 block">
                      {item.ai_category.replace(/_/g, ' ')}
                    </span>
                    <p className="font-body text-body-md text-on-surface-variant line-clamp-2">
                      {item.ai_summary}
                    </p>
                  </article>
                ))}
              </div>
            </>
          )}

          {/* Divider */}
          {(heroItem || secondaryItems.length > 0) && items.length > 0 && (
            <div className="border-t-2 border-outline-variant my-2" />
          )}

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 text-error p-4 bg-error-container/30 rounded">
              <span className="material-symbols-outlined text-lg">error</span>
              <span className="font-body text-sm">{error}</span>
              <button onClick={() => loadFeed()} className="ml-auto text-sm text-primary hover:underline bg-transparent border-none cursor-pointer">
                Retry
              </button>
            </div>
          )}

          {/* Loading skeleton */}
          {loading && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-4 border border-outline rounded animate-pulse">
                  <div className="flex gap-3">
                    <div className="w-10 h-10 rounded-full bg-surface-container" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3 bg-surface-container rounded w-1/4" />
                      <div className="h-4 bg-surface-container rounded w-3/4" />
                      <div className="h-3 bg-surface-container rounded w-full" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Feed list */}
          {!loading && items.length === 0 && !error && (
            <div className="flex flex-col items-center py-16 text-center">
              <span className="material-symbols-outlined text-5xl text-on-surface-variant mb-4">newspaper</span>
              <h3 className="text-lg font-headline text-on-surface mb-2">No articles found</h3>
              <p className="text-on-surface-variant font-body text-sm">
                {searchQuery ? 'Try a different search term.' : 'Articles will appear once collectors run.'}
              </p>
            </div>
          )}

          {!loading &&
            items.map((item) => <FeedCard key={item.id} item={item} showScore />)}

          {/* Load more */}
          {hasMore && !loading && (
            <button
              onClick={handleLoadMore}
              className="w-full py-3 text-center text-primary font-label uppercase tracking-wider text-sm hover:bg-surface-container transition-colors bg-transparent border border-primary cursor-pointer"
            >
              Load more articles
            </button>
          )}
        </div>

        {/* Right Sidebar */}
        <aside className="lg:col-span-4 flex flex-col gap-8">
          {/* Trending Tags */}
          {trending && trending.top_tags.length > 0 && (
            <div className="border border-primary bg-surface p-6">
              <div className="flex items-center gap-2 mb-6 border-b border-primary pb-4">
                <span className="material-symbols-outlined text-primary">monitoring</span>
                <h3 className="font-headline text-2xl uppercase tracking-wider text-primary">
                  Trending Tags
                </h3>
              </div>
              <div className="flex flex-col gap-3">
                {trending.top_tags.slice(0, 8).map((t, i) => (
                  <button
                    key={t.tag}
                    onClick={() => {
                      setSearchQuery('');
                      loadFeed({ tag: t.tag });
                    }}
                    className="flex justify-between items-center p-3 hover:bg-surface-container-high transition-colors cursor-pointer border border-transparent hover:border-outline-variant bg-transparent text-left"
                  >
                    <div>
                      <p className="font-headline text-lg text-primary">{t.tag}</p>
                      <p className="font-label text-sm text-secondary">{t.count} articles</p>
                    </div>
                    <span className="font-label text-xs text-on-surface-variant">#{i + 1}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Top Categories */}
          {trending && trending.top_categories.length > 0 && (
            <div className="border border-primary bg-surface p-6">
              <div className="flex items-center gap-2 mb-4 border-b border-primary pb-4">
                <span className="material-symbols-outlined text-primary">category</span>
                <h3 className="font-headline text-2xl uppercase tracking-wider text-primary">
                  Categories
                </h3>
              </div>
              <div className="flex flex-col gap-2">
                {trending.top_categories.map((c) => (
                  <button
                    key={c.category}
                    onClick={() => handleCategoryFilter(c.category)}
                    className="flex justify-between items-center p-2 hover:bg-surface-container transition-colors cursor-pointer bg-transparent border-none text-left"
                  >
                    <span className="font-label text-sm uppercase tracking-wider text-on-surface">
                      {c.category.replace(/_/g, ' ')}
                    </span>
                    <span className="font-label text-xs text-primary bg-primary-container px-2 py-0.5 rounded-full">
                      {c.count}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* System Status */}
          {status && (
            <div className="border border-primary bg-surface p-6">
              <h3 className="font-label text-label-md uppercase tracking-widest text-secondary mb-4 border-b border-outline-variant pb-2">
                System Status
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="font-headline text-3xl text-primary">{status.collected_events}</p>
                  <p className="font-label text-xs text-on-surface-variant uppercase">Collected</p>
                </div>
                <div>
                  <p className="font-headline text-3xl text-primary">{status.processed_events}</p>
                  <p className="font-label text-xs text-on-surface-variant uppercase">Processed</p>
                </div>
                <div>
                  <p className="font-headline text-3xl text-primary">{status.pipeline_coverage}%</p>
                  <p className="font-label text-xs text-on-surface-variant uppercase">Coverage</p>
                </div>
                <div>
                  <p className="font-headline text-3xl text-primary">{status.notifications}</p>
                  <p className="font-label text-xs text-on-surface-variant uppercase">Alerts</p>
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
