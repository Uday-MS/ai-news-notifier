import { useDocumentTitle } from '@/hooks/useDocumentTitle';

export default function OpportunitiesPage() {
  useDocumentTitle('Opportunities — Platinum Mist');

  return (
    <div className="p-6 md:p-12 lg:p-[64px] max-w-7xl mx-auto">
      <header className="mb-12 border-b-4 border-primary pb-6 flex justify-between items-end">
        <div>
          <h2 className="text-headline-lg font-headline text-primary uppercase">Active Opportunities</h2>
          <p className="text-body-lg text-on-surface-variant mt-2 max-w-2xl">Curated AI internships, fellowships, and research grants prioritized by your agent's capability matrix.</p>
        </div>
        <div className="hidden sm:flex gap-2">
          <span className="px-3 py-1 bg-surface-container-high border border-outline text-label-md font-label text-on-surface rounded-sm">All</span>
          <span className="px-3 py-1 bg-surface border border-outline text-label-md font-label text-on-surface rounded-sm hover:bg-surface-container cursor-pointer">Internships</span>
          <span className="px-3 py-1 bg-surface border border-outline text-label-md font-label text-on-surface rounded-sm hover:bg-surface-container cursor-pointer">Grants</span>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Featured */}
        <article className="col-span-1 md:col-span-2 lg:col-span-2 row-span-2 group relative border border-primary bg-surface-container-lowest overflow-hidden flex flex-col justify-between p-8 hover:bg-surface-container transition-colors duration-300">
          <div className="absolute top-0 right-0 p-4">
            <div className="flex items-center justify-center w-12 h-12 bg-primary text-on-primary rounded-full font-headline text-xl">98%</div>
          </div>
          <div className="z-10 relative mt-16">
            <div className="flex items-center gap-2 mb-4">
              <span className="px-2 py-1 bg-secondary-container text-on-secondary-container text-xs font-label uppercase tracking-widest border border-outline-variant rounded-sm">Research Fellowship</span>
              <span className="text-label-md font-label text-on-surface-variant">Closes in 5 Days</span>
            </div>
            <h3 className="text-[48px] leading-[1.1] font-headline text-primary mb-4 uppercase">DeepMind AI Alignment Scholar</h3>
            <p className="text-body-lg text-on-surface-variant max-w-xl mb-8">A fully funded 12-month fellowship focusing on scalable oversight and mechanistic interpretability. Open to PhD candidates and exceptional independent researchers.</p>
            <div className="flex items-center gap-4">
              <button className="px-8 py-3 bg-primary text-on-primary font-headline uppercase tracking-wide hover:bg-tertiary transition-colors border border-primary cursor-pointer">Review &amp; Apply</button>
              <button className="p-3 border border-primary text-primary hover:bg-surface-container-high transition-colors flex items-center justify-center cursor-pointer bg-transparent">
                <span className="material-symbols-outlined">bookmark_add</span>
              </button>
            </div>
          </div>
          <div className="absolute bottom-0 right-0 w-64 h-64 bg-surface-container-high rounded-tl-full opacity-50 z-0 border-l border-t border-outline-variant pointer-events-none" />
        </article>

        {/* Card 1 */}
        <article className="border border-primary bg-surface-container-lowest p-6 flex flex-col hover:bg-surface-container transition-colors relative group">
          <div className="flex justify-between items-start mb-4">
            <span className="px-2 py-1 bg-surface-variant text-on-surface text-xs font-label uppercase tracking-widest border border-outline-variant rounded-sm">Industry Internship</span>
            <span className="font-headline text-xl text-primary">85%</span>
          </div>
          <h3 className="text-headline-md font-headline text-primary mb-2 uppercase leading-tight">OpenAI ML Engineering Intern</h3>
          <p className="text-body-md text-on-surface-variant mb-6 flex-1">Summer 2024 cohort. Focus on large-scale distributed training infrastructure.</p>
          <div className="border-t border-outline-variant pt-4 flex justify-between items-center mt-auto">
            <span className="text-label-md font-label text-on-surface-variant flex items-center gap-1"><span className="material-symbols-outlined text-sm">calendar_today</span> Oct 15</span>
            <a className="text-primary font-headline uppercase tracking-wide hover:underline flex items-center gap-1" href="#">Apply <span className="material-symbols-outlined text-sm">arrow_forward</span></a>
          </div>
        </article>

        {/* Card 2 - Dark */}
        <article className="border border-primary bg-tertiary text-on-tertiary p-6 flex flex-col hover:bg-surface-container transition-colors relative group">
          <div className="flex justify-between items-start mb-4">
            <span className="px-2 py-1 bg-tertiary-container text-on-tertiary-container text-xs font-label uppercase tracking-widest border border-outline-variant rounded-sm">Seed Grant</span>
            <span className="font-headline text-xl text-on-tertiary">92%</span>
          </div>
          <h3 className="text-headline-md font-headline text-on-tertiary mb-2 uppercase leading-tight">Y Combinator AI Track</h3>
          <p className="text-body-md text-on-tertiary-container mb-6 flex-1">$500k standard deal for early-stage applied AI startups. Winter batch applications open.</p>
          <div className="border-t border-outline-variant pt-4 flex justify-between items-center mt-auto">
            <span className="text-label-md font-label text-on-tertiary-container flex items-center gap-1"><span className="material-symbols-outlined text-sm">calendar_today</span> Nov 1</span>
            <a className="text-on-tertiary font-headline uppercase tracking-wide hover:underline flex items-center gap-1" href="#">Draft App <span className="material-symbols-outlined text-sm">edit</span></a>
          </div>
        </article>

        {/* Card 3 */}
        <article className="border border-primary bg-surface-container-lowest p-6 flex flex-col hover:bg-surface-container transition-colors relative group">
          <div className="flex justify-between items-start mb-4">
            <span className="px-2 py-1 bg-surface-variant text-on-surface text-xs font-label uppercase tracking-widest border border-outline-variant rounded-sm">Academic Grant</span>
            <span className="font-headline text-xl text-primary">78%</span>
          </div>
          <h3 className="text-headline-md font-headline text-primary mb-2 uppercase leading-tight">NSF AI Institute Funding</h3>
          <p className="text-body-md text-on-surface-variant mb-6 flex-1">Collaborative research grants for trustworthy AI systems in critical infrastructure.</p>
          <div className="border-t border-outline-variant pt-4 flex justify-between items-center mt-auto">
            <span className="text-label-md font-label text-on-surface-variant flex items-center gap-1"><span className="material-symbols-outlined text-sm">calendar_today</span> Dec 12</span>
            <a className="text-primary font-headline uppercase tracking-wide hover:underline flex items-center gap-1" href="#">View <span className="material-symbols-outlined text-sm">visibility</span></a>
          </div>
        </article>
      </div>
    </div>
  );
}
