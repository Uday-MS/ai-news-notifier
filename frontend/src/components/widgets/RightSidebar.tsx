import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingModels } from './TrendingModels';
import { UpcomingDeadlines } from './UpcomingDeadlines';
import { SuggestedOrganizations } from './SuggestedOrganizations';
import { TRENDING_MODELS, DEADLINES, SUGGESTED_ORGANIZATIONS } from '@/utils/mockData';
import { getTrending, type TagCount } from '@/services/feedService';

export function RightSidebar() {
  const navigate = useNavigate();
  const [trendingTags, setTrendingTags] = useState<TagCount[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    getTrending(8).then((r) => { if (r.success && r.data) setTrendingTags(r.data.top_tags); });
  }, []);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (searchQuery.trim()) navigate(`/news?q=${encodeURIComponent(searchQuery.trim())}`);
  }

  return (
    <aside className="hidden xl:flex flex-col w-[350px] shrink-0 sticky top-0 h-screen overflow-y-auto no-scrollbar py-2 pl-6 pr-4 gap-4" role="complementary" aria-label="Sidebar">
      <form onSubmit={handleSearch} className="relative mt-1">
        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg">search</span>
        <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search"
          aria-label="Search AI News"
          className="w-full py-2.5 pl-10 pr-4 bg-[var(--c-elevated)] border-none rounded-full text-[15px] text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-primary focus:bg-surface transition-all" />
      </form>

      {trendingTags.length > 0 && (
        <div className="bg-[var(--c-raised)] rounded-2xl overflow-hidden">
          <h3 className="font-bold text-xl text-on-surface px-4 pt-3 pb-2">Trends for you</h3>
          <div className="flex flex-col">
            {trendingTags.slice(0, 5).map((tag, i) => (
              <button key={tag.tag} onClick={() => navigate(`/news?tag=${encodeURIComponent(tag.tag)}`)}
                className="flex justify-between items-start px-4 py-2.5 hover:bg-[var(--c-elevated)] transition-colors cursor-pointer bg-transparent border-none text-left w-full">
                <div>
                  <p className="text-[13px] text-on-surface-variant leading-4">{i + 1} · Trending in AI</p>
                  <p className="font-bold text-[15px] text-on-surface leading-5 mt-0.5">{tag.tag}</p>
                  <p className="text-[13px] text-on-surface-variant leading-4 mt-0.5">{tag.count} article{tag.count !== 1 ? 's' : ''}</p>
                </div>
                <span className="material-symbols-outlined text-on-surface-variant text-lg mt-1">more_horiz</span>
              </button>
            ))}
          </div>
          {trendingTags.length > 5 && (
            <button onClick={() => navigate('/news')} className="w-full px-4 py-3 text-left text-primary text-[15px] hover:bg-[var(--c-elevated)] transition-colors bg-transparent border-none cursor-pointer">Show more</button>
          )}
        </div>
      )}

      <TrendingModels models={TRENDING_MODELS.slice(0, 3)} />
      <UpcomingDeadlines deadlines={DEADLINES.slice(0, 3)} />
      <SuggestedOrganizations organizations={SUGGESTED_ORGANIZATIONS.slice(0, 3)} />

      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[13px] text-on-surface-variant px-1 pb-4">
        <a className="hover:underline" href="#">Terms</a>
        <a className="hover:underline" href="#">Privacy</a>
        <a className="hover:underline" href="#">Cookies</a>
        <a className="hover:underline" href="#">Accessibility</a>
        <span className="block w-full mt-1 text-on-surface-variant/60">© 2024 AI News Notifier</span>
      </div>
    </aside>
  );
}
