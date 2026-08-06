import { useState } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { cn } from '@/utils/cn';

type Filter = 'all' | 'internship' | 'grant';

const OPPORTUNITIES = [
  {
    type: 'fellowship' as const,
    filterType: 'grant' as Filter,
    featured: true,
    badge: 'Research Fellowship',
    closes: 'Closes in 5 Days',
    title: 'DeepMind AI Alignment Scholar',
    desc: 'A fully funded 12-month fellowship focusing on scalable oversight and mechanistic interpretability. Open to PhD candidates and exceptional independent researchers.',
    match: 98,
    cta: 'Review & Apply',
    url: 'https://deepmind.google/about/careers/',
    deadline: 'Oct 15',
  },
  {
    type: 'internship' as const,
    filterType: 'internship' as Filter,
    featured: false,
    badge: 'Industry Internship',
    title: 'OpenAI ML Engineering Intern',
    desc: 'Summer 2024 cohort. Focus on large-scale distributed training infrastructure.',
    match: 85,
    cta: 'Apply',
    url: 'https://openai.com/careers/',
    deadline: 'Oct 15',
  },
  {
    type: 'grant' as const,
    filterType: 'grant' as Filter,
    featured: false,
    badge: 'Seed Grant',
    title: 'Y Combinator AI Track',
    desc: '$500k standard deal for early-stage applied AI startups. Winter batch applications open.',
    match: 92,
    cta: 'Draft App',
    url: 'https://www.ycombinator.com/apply',
    deadline: 'Nov 1',
    dark: true,
  },
  {
    type: 'grant' as const,
    filterType: 'grant' as Filter,
    featured: false,
    badge: 'Academic Grant',
    title: 'NSF AI Institute Funding',
    desc: 'Collaborative research grants for trustworthy AI systems in critical infrastructure.',
    match: 78,
    cta: 'View',
    url: 'https://new.nsf.gov/funding/opportunities',
    deadline: 'Dec 12',
  },
];

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'internship', label: 'Internships' },
  { value: 'grant', label: 'Grants' },
];

export default function OpportunitiesPage() {
  useDocumentTitle('Opportunities — AI News Notifier');
  const [filter, setFilter] = useState<Filter>('all');
  const [bookmarked, setBookmarked] = useState<Set<string>>(new Set());

  const filtered = filter === 'all' ? OPPORTUNITIES : OPPORTUNITIES.filter((o) => o.filterType === filter);
  const featuredOpp = filtered.find((o) => o.featured);
  const others = filtered.filter((o) => !o.featured);

  function toggleBookmark(title: string) {
    setBookmarked((prev) => {
      const next = new Set(prev);
      if (next.has(title)) next.delete(title);
      else next.add(title);
      return next;
    });
  }

  return (
    <div className="p-6 md:p-12 lg:p-[64px] max-w-7xl mx-auto">
      <header className="mb-12 border-b-4 border-primary pb-6 flex justify-between items-end">
        <div>
          <h2 className="text-headline-lg font-headline text-primary uppercase">Active Opportunities</h2>
          <p className="text-body-lg text-on-surface-variant mt-2 max-w-2xl">Curated AI internships, fellowships, and research grants prioritized by your interest profile.</p>
        </div>
        <div className="hidden sm:flex gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={cn(
                'px-3 py-1 text-label-md font-label rounded-sm border cursor-pointer transition-colors',
                filter === f.value
                  ? 'bg-surface-container-high border-primary text-primary font-bold'
                  : 'bg-surface border-outline text-on-surface hover:bg-surface-container'
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Featured */}
        {featuredOpp && (
          <article className="col-span-1 md:col-span-2 lg:col-span-2 row-span-2 group relative border border-primary bg-surface-container-lowest overflow-hidden flex flex-col justify-between p-8 hover:bg-surface-container transition-colors duration-300">
            <div className="absolute top-0 right-0 p-4">
              <div className="flex items-center justify-center w-12 h-12 bg-primary text-on-primary rounded-full font-headline text-xl">{featuredOpp.match}%</div>
            </div>
            <div className="z-10 relative mt-16">
              <div className="flex items-center gap-2 mb-4">
                <span className="px-2 py-1 bg-secondary-container text-on-secondary-container text-xs font-label uppercase tracking-widest border border-outline-variant rounded-sm">{featuredOpp.badge}</span>
                <span className="text-label-md font-label text-on-surface-variant">{featuredOpp.closes}</span>
              </div>
              <h3 className="text-[48px] leading-[1.1] font-headline text-primary mb-4 uppercase">{featuredOpp.title}</h3>
              <p className="text-body-lg text-on-surface-variant max-w-xl mb-8">{featuredOpp.desc}</p>
              <div className="flex items-center gap-4">
                <button
                  onClick={() => window.open(featuredOpp.url, '_blank')}
                  className="px-8 py-3 bg-primary text-on-primary font-headline uppercase tracking-wide hover:bg-tertiary transition-colors border border-primary cursor-pointer"
                >
                  {featuredOpp.cta}
                </button>
                <button
                  onClick={() => toggleBookmark(featuredOpp.title)}
                  className={cn(
                    'p-3 border border-primary hover:bg-surface-container-high transition-colors flex items-center justify-center cursor-pointer bg-transparent',
                    bookmarked.has(featuredOpp.title) && 'text-primary'
                  )}
                >
                  <span className={cn('material-symbols-outlined', bookmarked.has(featuredOpp.title) && 'icon-fill')}>bookmark</span>
                </button>
              </div>
            </div>
            <div className="absolute bottom-0 right-0 w-64 h-64 bg-surface-container-high rounded-tl-full opacity-50 z-0 border-l border-t border-outline-variant pointer-events-none" />
          </article>
        )}

        {/* Other Cards */}
        {others.map((opp) => (
          <article
            key={opp.title}
            className={cn(
              'border border-primary p-6 flex flex-col hover:bg-surface-container transition-colors relative group',
              opp.dark ? 'bg-tertiary text-on-tertiary' : 'bg-surface-container-lowest'
            )}
          >
            <div className="flex justify-between items-start mb-4">
              <span className={cn(
                'px-2 py-1 text-xs font-label uppercase tracking-widest border rounded-sm',
                opp.dark ? 'bg-tertiary-container text-on-tertiary-container border-outline-variant' : 'bg-surface-variant text-on-surface border-outline-variant'
              )}>
                {opp.badge}
              </span>
              <span className={cn('font-headline text-xl', opp.dark ? 'text-on-tertiary' : 'text-primary')}>{opp.match}%</span>
            </div>
            <h3 className={cn('text-headline-md font-headline mb-2 uppercase leading-tight', opp.dark ? 'text-on-tertiary' : 'text-primary')}>
              {opp.title}
            </h3>
            <p className={cn('text-body-md mb-6 flex-1', opp.dark ? 'text-on-tertiary-container' : 'text-on-surface-variant')}>{opp.desc}</p>
            <div className="border-t border-outline-variant pt-4 flex justify-between items-center mt-auto">
              <span className={cn('text-label-md font-label flex items-center gap-1', opp.dark ? 'text-on-tertiary-container' : 'text-on-surface-variant')}>
                <span className="material-symbols-outlined text-sm">calendar_today</span> {opp.deadline}
              </span>
              <button
                onClick={() => window.open(opp.url, '_blank')}
                className={cn(
                  'font-headline uppercase tracking-wide hover:underline flex items-center gap-1 bg-transparent border-none cursor-pointer',
                  opp.dark ? 'text-on-tertiary' : 'text-primary'
                )}
              >
                {opp.cta} <span className="material-symbols-outlined text-sm">arrow_forward</span>
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
