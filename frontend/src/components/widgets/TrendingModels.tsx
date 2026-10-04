/**
 * TopCategories — Intelligence category breakdown from backend.
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
    <div className="card-intel overflow-hidden">
      <div className="px-3 pt-3 pb-2 border-b border-outline-variant">
        <h3 className="type-mono-label text-[var(--c-text-3)]">Categories</h3>
      </div>
      <div className="flex flex-col">
        {categories.slice(0, 5).map((cat) => (
          <button
            key={cat.category}
            onClick={() => navigate(`/news?category=${encodeURIComponent(cat.category)}`)}
            className="flex items-center gap-2.5 px-3 py-2 hover:bg-[var(--c-elevated)] transition-colors cursor-pointer bg-transparent border-none text-left w-full"
          >
            <span className="material-symbols-outlined text-[var(--c-text-3)] text-base">
              {categoryIcon(cat.category)}
            </span>
            <div className="flex-1 min-w-0">
              <p className="font-headline font-medium text-[13px] text-on-surface leading-5 capitalize tracking-tight">
                {cat.category.replace(/_/g, ' ')}
              </p>
            </div>
            <span className="font-mono text-[11px] text-[var(--c-text-3)] tabular-nums">
              {cat.count}
            </span>
          </button>
        ))}
      </div>
      {categories.length > 5 && (
        <button
          onClick={() => navigate('/news')}
          className="w-full px-3 py-2.5 text-left text-primary text-[13px] font-medium hover:bg-[var(--c-elevated)] transition-colors bg-transparent border-none cursor-pointer border-t border-outline-variant"
        >
          All categories →
        </button>
      )}
    </div>
  );
}
