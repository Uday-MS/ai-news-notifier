/**
 * RightSidebar — Intelligence inspector panel.
 * Search, trending signals, categories, top stories.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TopCategories } from './TrendingModels';
import { TopStories } from './SuggestedOrganizations';
import { getTrending, getCategories, type TagCount, type CategoryCount, type FeedItem } from '@/services/feedService';

export function RightSidebar() {
  const navigate = useNavigate();
  const [trendingTags, setTrendingTags] = useState<TagCount[]>([]);
  const [categories, setCategories] = useState<CategoryCount[]>([]);
  const [topStories, setTopStories] = useState<FeedItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    getTrending(8).then((r) => {
      if (r.success && r.data) {
        setTrendingTags(r.data.top_tags);
        setTopStories(r.data.most_important ?? []);
      }
    });
    getCategories(10).then((r) => {
      if (r.success && r.data) setCategories(r.data);
    });
  }, []);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (searchQuery.trim()) navigate(`/news?q=${encodeURIComponent(searchQuery.trim())}`);
  }

  return (
    <aside
      className="hidden xl:flex flex-col w-[340px] shrink-0 sticky top-0 h-screen overflow-y-auto no-scrollbar py-3 pl-5 pr-4 gap-3"
      role="complementary"
      aria-label="Intelligence sidebar"
    >
      {/* Search */}
      <form onSubmit={handleSearch} className="relative mt-0.5">
        <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--c-text-3)] text-base">
          search
        </span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search intelligence..."
          aria-label="Search AI Intelligence"
          className="w-full py-2 pl-9 pr-3 bg-[var(--c-elevated)] border border-[var(--c-border-subtle)] rounded text-[13px] text-on-surface placeholder:text-[var(--c-text-3)] focus:outline-none focus:border-primary transition-colors font-body"
        />
      </form>

      {/* Trending Signals */}
      {trendingTags.length > 0 && (
        <div className="card-intel overflow-hidden">
          <div className="px-3 pt-3 pb-2 border-b border-outline-variant">
            <h3 className="type-mono-label text-[var(--c-text-3)]">Trending Signals</h3>
          </div>
          <div className="flex flex-col">
            {trendingTags.slice(0, 5).map((tag, i) => (
              <button
                key={tag.tag}
                onClick={() => navigate(`/news?tag=${encodeURIComponent(tag.tag)}`)}
                className="flex justify-between items-start px-3 py-2.5 hover:bg-[var(--c-elevated)] transition-colors cursor-pointer bg-transparent border-none text-left w-full"
              >
                <div>
                  <p className="type-mono-tag text-[var(--c-text-3)]">{String(i + 1).padStart(2, '0')} · AI</p>
                  <p className="font-headline font-semibold text-[14px] text-on-surface leading-5 mt-0.5 tracking-tight">
                    {tag.tag}
                  </p>
                  <p className="font-mono text-[11px] text-[var(--c-text-3)] leading-4 mt-0.5 tabular-nums">
                    {tag.count} signal{tag.count !== 1 ? 's' : ''}
                  </p>
                </div>
              </button>
            ))}
          </div>
          {trendingTags.length > 5 && (
            <button
              onClick={() => navigate('/news')}
              className="w-full px-3 py-2.5 text-left text-primary text-[13px] font-medium hover:bg-[var(--c-elevated)] transition-colors bg-transparent border-none cursor-pointer border-t border-outline-variant"
            >
              View all signals →
            </button>
          )}
        </div>
      )}

      <TopCategories categories={categories} />
      <TopStories stories={topStories} />

      {/* Footer */}
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-[var(--c-text-4)] px-1 pb-4 font-mono uppercase tracking-wider mt-auto">
        <span>Terms</span>
        <span>Privacy</span>
        <span>Docs</span>
        <span className="block w-full mt-1">© {new Date().getFullYear()} NexusAI</span>
      </div>
    </aside>
  );
}
