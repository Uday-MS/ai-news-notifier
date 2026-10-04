import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { FeedCard } from '@/components/feed/FeedCard';
import { searchFeed, getTrending, type FeedItem, type TrendingResponse, type SearchParams } from '@/services/feedService';

export default function ResearchPage() {
  useDocumentTitle('Research — NexusAI');
  const navigate = useNavigate();
  const [items, setItems] = useState<FeedItem[]>([]);
  const [trending, setTrending] = useState<TrendingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [hasMore, setHasMore] = useState(false);

  const loadResearch = useCallback(async (params: SearchParams = {}, append = false) => {
    if (!append) setLoading(true);
    setError('');
    try {
      const result = await searchFeed({ category: 'ai_research', sort: 'highest_importance', limit: 20, ...params });
      if (result.success && result.data) {
        setItems((prev) => append ? [...prev, ...result.data!.items] : result.data!.items);
        setHasMore(result.data.pagination.has_more);
      }
    } catch { setError('Failed to load research.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    loadResearch();
    getTrending(5).then((r) => r.success && r.data && setTrending(r.data));
  }, [loadResearch]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    loadResearch(searchQuery.trim() ? { q: searchQuery.trim() } : {});
  }

  const topResearch = !loading && items.length > 0 ? items[0] : null;
  const restItems = !loading && items.length > 1 ? items.slice(1) : [];

  return (
    <div className="flex flex-col min-h-screen">
      <div className="sticky top-0 z-10 bg-surface/90 backdrop-blur-md border-b border-outline-variant">
        <div className="px-4 py-2.5">
          <h2 className="font-headline font-semibold text-[16px] text-on-surface tracking-tight">Research</h2>
        </div>
        <form onSubmit={handleSearch} className="px-4 pb-2.5">
          <div className="relative">
            <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--c-text-3)] text-base">search</span>
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search research papers..."
              className="w-full py-2 pl-9 pr-3 bg-[var(--c-elevated)] border border-[var(--c-border-subtle)] rounded text-[13px] text-on-surface placeholder:text-[var(--c-text-3)] focus:outline-none focus:border-primary transition-colors font-body" />
          </div>
        </form>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-[var(--c-danger)] px-4 py-3 bg-[var(--c-danger-dim)] border-b border-outline-variant">
          <span className="material-symbols-outlined text-base">error</span>
          <span className="text-[13px] font-body">{error}</span>
          <button onClick={() => loadResearch()} className="ml-auto text-[12px] font-mono text-primary uppercase tracking-wider hover:underline bg-transparent border-none cursor-pointer">Retry</button>
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
            <span className="material-symbols-outlined text-2xl text-[var(--c-text-3)]">science</span>
          </div>
          <h3 className="font-headline font-semibold text-[16px] text-on-surface mb-1.5 tracking-tight">No research found</h3>
          <p className="text-[var(--c-text-2)] text-[13px] max-w-xs font-body">{searchQuery ? 'Try a different search term.' : 'Research papers will appear once collectors run.'}</p>
        </div>
      )}

      {/* Featured research */}
      {topResearch && (
        <div className="border-b border-outline-variant">
          <a href={topResearch.source_url} target="_blank" rel="noopener noreferrer"
            className="block px-4 py-4 bg-[var(--c-secondary-dim)] hover:bg-secondary/10 transition-colors no-underline">
            <div className="flex items-center gap-2 mb-2">
              <span className="badge badge-secondary">Top Research</span>
              <span className="font-mono text-[10px] text-[var(--c-text-3)] uppercase tracking-wider">{topResearch.organization}</span>
              {topResearch.importance_score > 0 && (
                <span className="badge badge-primary ml-auto">IMP {topResearch.importance_score}</span>
              )}
            </div>
            <h3 className="font-headline font-semibold text-[15px] text-on-surface leading-snug mb-1.5 tracking-tight">{topResearch.cleaned_title}</h3>
            <p className="text-[13px] text-[var(--c-text-2)] leading-[1.45] line-clamp-3 font-body">{topResearch.ai_summary}</p>
            {topResearch.ai_tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {topResearch.ai_tags.slice(0, 5).map((tag) => (
                  <span key={tag} className="badge badge-neutral !text-[9px]">{tag}</span>
                ))}
              </div>
            )}
          </a>
        </div>
      )}

      {trending && !loading && items.length > 0 && (
        <div className="px-4 py-2 border-b border-outline-variant flex items-center gap-1.5">
          <span className="font-mono text-[10px] text-[var(--c-text-3)] uppercase tracking-wider">
            {items.length} papers loaded
            {trending.total_ready > 0 && ` · ${trending.total_ready} total`}
          </span>
        </div>
      )}

      <div className="flex flex-col page-transition">
        {restItems.map((item) => <FeedCard key={item.id} item={item} showScore score={item.importance_score} />)}
      </div>

      {hasMore && !loading && (
        <button onClick={() => loadResearch({ q: searchQuery.trim() || undefined, offset: items.length }, true)}
          className="w-full py-3.5 text-center text-primary font-mono text-[12px] font-medium uppercase tracking-wider hover:bg-[var(--c-elevated)] transition-colors bg-transparent border-none border-t border-outline-variant cursor-pointer">
          Load more →
        </button>
      )}
    </div>
  );
}
