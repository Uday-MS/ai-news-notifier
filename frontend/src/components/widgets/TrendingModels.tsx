/**
 * TopCategories — shows real category breakdown from the backend.
 * Replaces the old mock TrendingModels widget.
 */

import { useNavigate } from 'react-router-dom';
import type { CategoryCount } from '@/services/feedService';

interface TopCategoriesProps {
  categories: CategoryCount[];
}

function categoryIcon(category: string): string {
  const map: Record<string, string> = {
    ai_model: 'smart_toy',
    ai_research: 'biotech',
    product_release: 'rocket_launch',
    open_source: 'code',
    startup: 'storefront',
    funding: 'payments',
    hackathon: 'emoji_events',
    internship: 'school',
    competition: 'trophy',
    student_program: 'school',
    security: 'shield',
    other: 'article',
  };
  return map[category] ?? 'article';
}

export function TopCategories({ categories }: TopCategoriesProps) {
  const navigate = useNavigate();

  if (categories.length === 0) return null;

  return (
    <div className="bg-[var(--c-raised)] rounded-2xl overflow-hidden">
      <h3 className="font-bold text-xl text-on-surface px-4 pt-3 pb-2">Top Categories</h3>
      <div className="flex flex-col">
        {categories.slice(0, 5).map((cat) => (
          <button
            key={cat.category}
            onClick={() => navigate(`/news?category=${encodeURIComponent(cat.category)}`)}
            className="flex items-center gap-3 px-4 py-2.5 hover:bg-[var(--c-elevated)] transition-colors cursor-pointer bg-transparent border-none text-left w-full"
          >
            <span className="material-symbols-outlined text-on-surface-variant text-lg">
              {categoryIcon(cat.category)}
            </span>
            <div className="flex-1 min-w-0">
              <p className="font-bold text-[15px] text-on-surface leading-5 capitalize">
                {cat.category.replace(/_/g, ' ')}
              </p>
              <p className="text-[13px] text-on-surface-variant leading-4">
                {cat.count} article{cat.count !== 1 ? 's' : ''}
              </p>
            </div>
          </button>
        ))}
      </div>
      {categories.length > 5 && (
        <button
          onClick={() => navigate('/news')}
          className="w-full px-4 py-3 text-left text-primary text-[15px] hover:bg-[var(--c-elevated)] transition-colors bg-transparent border-none cursor-pointer"
        >
          Show more
        </button>
      )}
    </div>
  );
}
