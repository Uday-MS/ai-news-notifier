import { TrendingModels } from './TrendingModels';
import { UpcomingDeadlines } from './UpcomingDeadlines';
import { RecommendedTopics } from './RecommendedTopics';
import { SuggestedOrganizations } from './SuggestedOrganizations';
import { TRENDING_MODELS, DEADLINES, RECOMMENDED_TOPICS, SUGGESTED_ORGANIZATIONS } from '@/utils/mockData';

/**
 * Right sidebar — search bar + widgets.
 * Visible only on xl+ screens, sticky within its column.
 */
export function RightSidebar() {
  return (
    <aside className="hidden xl:flex flex-col w-[350px] shrink-0 sticky top-0 h-screen overflow-y-auto no-scrollbar py-3 pl-6 pr-6 gap-4">
      {/* Search */}
      <div className="relative">
        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-xl">
          search
        </span>
        <input
          type="text"
          placeholder="Search AI News"
          className="w-full py-2.5 pl-11 pr-4 bg-surface-container border border-transparent rounded-full text-body-md font-body text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:border-primary focus:bg-surface transition-colors"
        />
      </div>

      {/* Widgets */}
      <TrendingModels models={TRENDING_MODELS} />
      <UpcomingDeadlines deadlines={DEADLINES} />
      <SuggestedOrganizations organizations={SUGGESTED_ORGANIZATIONS} />
      <RecommendedTopics topics={RECOMMENDED_TOPICS} />

      {/* Footer */}
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-label-sm font-body text-on-surface-variant px-1 pb-4">
        <a className="hover:underline" href="#">Terms</a>
        <a className="hover:underline" href="#">Privacy</a>
        <a className="hover:underline" href="#">Cookies</a>
        <a className="hover:underline" href="#">Accessibility</a>
        <span className="block w-full mt-1 text-on-surface-variant/60">© 2024 AI News Notifier</span>
      </div>
    </aside>
  );
}
