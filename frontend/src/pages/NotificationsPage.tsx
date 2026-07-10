import { useDocumentTitle } from '@/hooks/useDocumentTitle';

export default function NotificationsPage() {
  useDocumentTitle('Notifications — Platinum Mist');

  return (
    <div className="p-8 md:p-[64px]">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between border-b-2 border-primary pb-6 mb-12">
        <div>
          <h2 className="font-headline text-5xl md:text-7xl text-primary uppercase tracking-wide leading-none">Notifications</h2>
          <p className="font-label text-secondary mt-2">SYSTEM ALERTS &amp; MATCHES</p>
        </div>
        <button className="mt-6 md:mt-0 px-6 py-2 border border-primary text-primary font-label uppercase hover:bg-primary hover:text-on-primary transition-colors flex items-center gap-2 bg-transparent cursor-pointer">
          <span className="material-symbols-outlined text-sm">done_all</span> Mark all as read
        </button>
      </div>

      <div className="max-w-4xl mx-auto space-y-12 pb-24">
        {/* Today */}
        <section>
          <div className="flex items-center gap-4 mb-6">
            <h3 className="font-label text-xl text-primary font-bold uppercase tracking-widest">Today</h3>
            <div className="flex-1 h-px bg-outline-variant" />
          </div>
          <div className="space-y-4">
            {/* Unread: Research */}
            <div className="group relative bg-surface-container-lowest border-2 border-primary p-6 rounded flex flex-col sm:flex-row gap-6 items-start hover:shadow-[4px_4px_0px_#16191e] transition-all">
              <div className="absolute top-0 right-0 w-3 h-3 bg-primary transform translate-x-1.5 -translate-y-1.5 rotate-45" />
              <div className="w-12 h-12 shrink-0 bg-surface-container border border-outline flex items-center justify-center rounded-sm">
                <span className="material-symbols-outlined text-primary">science</span>
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-headline text-2xl text-primary uppercase">New Research Paper Match</h4>
                  <span className="font-label text-sm text-secondary">10:42 AM</span>
                </div>
                <p className="font-body text-lg text-on-surface-variant mb-4 max-w-2xl">System identified a high-confidence match for your query parameters in the newly published paper: "Generative Models in Constrained Environments."</p>
                <div className="flex gap-3">
                  <button className="px-4 py-1.5 bg-primary text-on-primary font-label text-sm uppercase hover:bg-tertiary transition-colors border-none cursor-pointer">View Paper</button>
                  <button className="px-4 py-1.5 border border-outline text-secondary font-label text-sm uppercase hover:bg-surface-container transition-colors bg-transparent cursor-pointer">Dismiss</button>
                </div>
              </div>
            </div>
            {/* Unread: System */}
            <div className="group relative bg-surface-container-lowest border-2 border-primary p-6 rounded flex flex-col sm:flex-row gap-6 items-start hover:shadow-[4px_4px_0px_#16191e] transition-all">
              <div className="absolute top-0 right-0 w-3 h-3 bg-primary transform translate-x-1.5 -translate-y-1.5 rotate-45" />
              <div className="w-12 h-12 shrink-0 bg-surface-container border border-outline flex items-center justify-center rounded-sm">
                <span className="material-symbols-outlined text-error">warning</span>
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-headline text-2xl text-primary uppercase">System Alert: API Rate Limit</h4>
                  <span className="font-label text-sm text-secondary">08:15 AM</span>
                </div>
                <p className="font-body text-lg text-on-surface-variant max-w-2xl">Command execution paused. You have reached 95% of your hourly OpenAI API quota. Adjust parameters to prevent throttling.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Yesterday */}
        <section>
          <div className="flex items-center gap-4 mb-6">
            <h3 className="font-label text-xl text-secondary uppercase tracking-widest">Yesterday</h3>
            <div className="flex-1 h-px bg-outline-variant" />
          </div>
          <div className="space-y-4">
            <div className="group relative bg-surface border border-outline p-6 rounded flex flex-col sm:flex-row gap-6 items-start opacity-80 hover:opacity-100 transition-opacity">
              <div className="w-12 h-12 shrink-0 bg-surface-container-lowest border border-outline-variant flex items-center justify-center rounded-sm"><span className="material-symbols-outlined text-secondary">code</span></div>
              <div className="flex-1">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-headline text-xl text-secondary uppercase">Repository Update</h4>
                  <span className="font-label text-sm text-tertiary">Yesterday, 16:30</span>
                </div>
                <p className="font-body text-base text-secondary mb-3 max-w-2xl">Main branch of tracked repository 'neo-brutalism-ui' had 4 new commits. Auto-build initiated successfully.</p>
                <a className="font-label text-sm text-primary uppercase underline hover:no-underline flex items-center gap-1 w-max" href="#">View Commits <span className="material-symbols-outlined text-sm">arrow_forward</span></a>
              </div>
            </div>
            <div className="group relative bg-surface border border-outline p-6 rounded flex flex-col sm:flex-row gap-6 items-start opacity-80 hover:opacity-100 transition-opacity">
              <div className="w-12 h-12 shrink-0 bg-surface-container-lowest border border-outline-variant flex items-center justify-center rounded-sm"><span className="material-symbols-outlined text-secondary">bookmark</span></div>
              <div className="flex-1">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-headline text-xl text-secondary uppercase">Resource Saved</h4>
                  <span className="font-label text-sm text-tertiary">Yesterday, 11:05</span>
                </div>
                <p className="font-body text-base text-secondary max-w-2xl">"Architectural Patterns in LLM Agents" was successfully added to your Saved collection.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
