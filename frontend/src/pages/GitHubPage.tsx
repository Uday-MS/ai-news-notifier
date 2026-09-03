import { useState, useEffect, useCallback } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { FeedCard } from '@/components/feed/FeedCard';
import { searchFeed, type FeedItem, type SearchParams } from '@/services/feedService';

export default function GitHubPage() {
  useDocumentTitle('GitHub & Open Source — AI News Notifier');
  const [items, setItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [hasMore, setHasMore] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  const loadRepos = useCallback(async (params: SearchParams = {}, append = false) => {
    if (!append) setLoading(true);
    setError('');
    try {
      const result = await searchFeed({
        category: 'open_source',
        sort: 'highest_importance',
        limit: 20,
        ...params,
      });
      if (result.success && result.data) {
        setItems((prev) => append ? [...prev, ...result.data!.items] : result.data!.items);
        setHasMore(result.data.pagination.has_more);
        setTotalCount(result.data.pagination.total);
      }
    } catch {
      setError('Failed to load open source articles.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRepos();
  }, [loadRepos]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    loadRepos(searchQuery.trim() ? { q: searchQuery.trim() } : {});
  }

  const topItem = !loading && items.length > 0 ? items[0] : null;
  const restItems = !loading && items.length > 1 ? items.slice(1) : [];

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-surface/95 backdrop-blur-md border-b border-outline">
        <div className="px-4 py-2.5">
          <h2 className="text-xl font-bold text-on-surface">GitHub & Open Source</h2>
          <p className="text-[13px] text-on-surface-variant mt-0.5">AI open source projects, releases, and repository updates</p>
        </div>
        <form onSubmit={handleSearch} className="px-4 pb-3">
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg">search</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search open source projects..."
              className="w-full py-2.5 pl-10 pr-4 bg-[var(--c-elevated)] border-none rounded-full text-[15px] text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary focus:bg-surface transition-all"
            />
          </div>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-error px-4 py-3 bg-error-container/30">
          <span className="material-symbols-outlined text-lg">error</span>
          <span className="text-sm">{error}</span>
          <button onClick={() => loadRepos()} className="ml-auto text-sm text-primary hover:underline bg-transparent border-none cursor-pointer">Retry</button>
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
          <span className="material-symbols-outlined text-5xl text-on-surface-variant mb-4">code</span>
          <h3 className="text-lg font-bold text-on-surface mb-2">No open source articles found</h3>
          <p className="text-on-surface-variant text-sm max-w-xs">
            {searchQuery ? 'Try a different search term.' : 'Open source project updates will appear as collectors run.'}
          </p>
        </div>
      )}

      {/* Featured */}
      {topItem && (
        <div className="border-b border-outline">
          <a
            href={topItem.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="block px-4 py-4 bg-primary/5 hover:bg-primary/10 transition-colors no-underline"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 bg-primary text-on-primary text-[11px] font-bold rounded-full">FEATURED</span>
              <span className="text-[13px] text-on-surface-variant">{topItem.organization}</span>
              {topItem.importance_score > 0 && (
                <span className="ml-auto text-[13px] font-medium text-primary">{topItem.importance_score}% relevance</span>
              )}
            </div>
            <h3 className="text-[17px] font-bold text-on-surface leading-snug mb-1">{topItem.cleaned_title}</h3>
            <p className="text-[14px] text-on-surface-variant leading-[1.4] line-clamp-3">{topItem.ai_summary}</p>
            {topItem.ai_tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {topItem.ai_tags.slice(0, 5).map((tag) => (
                  <span key={tag} className="text-[12px] text-primary bg-primary/5 px-2 py-0.5 rounded-full">{tag}</span>
                ))}
              </div>
            )}
          </a>
        </div>
      )}

      {/* Stats */}
      {!loading && items.length > 0 && (
        <div className="px-4 py-2 border-b border-outline text-[13px] text-on-surface-variant flex items-center gap-1.5">
          <span className="material-symbols-outlined text-sm">code</span>
          {totalCount} open source article{totalCount !== 1 ? 's' : ''}
        </div>
      )}

      {/* Feed */}
      <div className="flex flex-col page-transition">
        {restItems.map((item) => (
          <FeedCard key={item.id} item={item} showScore score={item.importance_score} />
        ))}
      </div>

      {/* Load more */}
      {hasMore && !loading && (
        <button
          onClick={() => loadRepos({ q: searchQuery.trim() || undefined, offset: items.length }, true)}
          className="w-full py-4 text-center text-primary font-semibold text-[15px] hover:bg-[var(--c-raised)] transition-colors bg-transparent border-none border-t border-outline cursor-pointer"
        >
          Show more
        </button>
      )}
    </div>
  );
}
