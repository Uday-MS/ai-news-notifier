import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingModels } from './TrendingModels';
import { UpcomingDeadlines } from './UpcomingDeadlines';
import { SuggestedOrganizations } from './SuggestedOrganizations';
import { TRENDING_MODELS, DEADLINES, SUGGESTED_ORGANIZATIONS } from '@/utils/mockData';
import { getTrending, type TagCount } from '@/services/feedService';

/**
 * Right sidebar — search bar + widgets with live trending topics.
 * Visible only on xl+ screens, sticky within its column.
 */
export function RightSidebar() {
  const navigate = useNavigate();
  const [trendingTags, setTrendingTags] = useState<TagCount[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    getTrending(8).then((r) => {
      if (r.success && r.data) {
        setTrendingTags(r.data.top_tags);
      }
    });
  }, []);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/news?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  }

  return (
    <aside
      className="hidden xl:flex flex-col w-[350px] shrink-0 sticky top-0 h-screen overflow-y-auto no-scrollbar py-3 pl-5 pr-5 gap-3"
      role="complementary"
      aria-label="Sidebar"
    >
      {/* Search */}
      <form onSubmit={handleSearch} className="relative">
        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-xl">
          search
        </span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search AI News"
          aria-label="Search AI News"
          className="w-full py-2.5 pl-11 pr-4 bg-surface-container border border-transparent rounded-full text-body-md font-body text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:border-primary focus:bg-surface transition-colors"
        />
      </form>

      {/* Live Trending Topics */}
      {trendingTags.length > 0 && (
        <div className="bg-surface-container rounded-2xl py-3">
          <h3 className="font-body font-bold text-lg text-on-surface px-4 mb-2">Trending in AI</h3>
          <div className="flex flex-col">
            {trendingTags.slice(0, 6).map((tag, i) => (
              <button
                key={tag.tag}
                onClick={() => navigate(`/news?tag=${encodeURIComponent(tag.tag)}`)}
                className="flex justify-between items-center px-4 py-2 hover:bg-surface-container-high rounded-lg transition-colors cursor-pointer bg-transparent border-none text-left"
              >
                <div>
                  <p className="font-body text-xs text-on-surface-variant">
                    {i + 1} · Trending
                  </p>
                  <p className="font-body font-bold text-[14px] text-on-surface leading-snug">
                    #{tag.tag}
                  </p>
                  <p className="font-body text-xs text-on-surface-variant">
                    {tag.count} article{tag.count !== 1 ? 's' : ''}
                  </p>
                </div>
                <span className="material-symbols-outlined text-on-surface-variant text-lg">more_horiz</span>
              </button>
            ))}
          </div>
          {trendingTags.length > 6 && (
            <button
              onClick={() => navigate('/news')}
              className="w-full px-4 py-2 text-left text-primary text-sm font-body hover:bg-surface-container-high rounded-b-2xl transition-colors bg-transparent border-none cursor-pointer"
            >
              Show more
            </button>
          )}
        </div>
      )}

      {/* Static widgets */}
      <TrendingModels models={TRENDING_MODELS.slice(0, 3)} />
      <UpcomingDeadlines deadlines={DEADLINES.slice(0, 3)} />
      <SuggestedOrganizations organizations={SUGGESTED_ORGANIZATIONS.slice(0, 3)} />

      {/* Footer */}
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-label-sm font-body text-on-surface-variant px-1 pb-4 mt-1">
        <a className="hover:underline" href="#">Terms</a>
        <a className="hover:underline" href="#">Privacy</a>
        <a className="hover:underline" href="#">Cookies</a>
        <a className="hover:underline" href="#">Accessibility</a>
        <span className="block w-full mt-1 text-on-surface-variant/60">© 2024 AI News Notifier</span>
      </div>
    </aside>
  );
}
