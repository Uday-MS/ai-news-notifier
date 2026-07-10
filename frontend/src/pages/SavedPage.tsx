import { useDocumentTitle } from '@/hooks/useDocumentTitle';

export default function SavedPage() {
  useDocumentTitle('Saved Archive — Platinum Mist');

  const logs = [
    { icon: 'link', title: 'GitHub: microsoft/autogen-studio', desc: 'UI interface for defining and managing multi-agent workflows.' },
    { icon: 'terminal', title: 'Snippet: Rust bindings for local LLM inference', desc: 'Optimized memory allocation for concurrent model loads.' },
    { icon: 'lightbulb', title: 'Idea: Asymmetric Encryption in Agent Comms', desc: 'Draft protocol for securing inter-agent data passing.' },
  ];

  return (
    <div className="flex flex-col flex-1">
      {/* Header */}
      <header className="px-8 pt-12 pb-6 border-b border-primary bg-surface-container-lowest sticky top-0 z-20">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 max-w-7xl mx-auto w-full">
          <div>
            <h1 className="text-headline-lg font-headline uppercase text-primary">Saved Archive</h1>
            <p className="text-body-md text-on-surface-variant mt-2 max-w-xl">Your curated repository of critical intelligence, structural research, and deployment opportunities. Organized for rapid retrieval.</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative group">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline group-focus-within:text-primary transition-colors">search</span>
              <input className="pl-10 pr-4 py-2 bg-surface-container border border-primary text-body-md font-body focus:outline-none focus:ring-1 focus:ring-primary w-64 transition-all" placeholder="Query archive..." type="text" />
            </div>
            <button className="p-2 border border-primary hover:bg-surface-container transition-colors flex items-center justify-center text-primary bg-transparent cursor-pointer"><span className="material-symbols-outlined">tune</span></button>
          </div>
        </div>
        <div className="mt-8 flex gap-3 overflow-x-auto no-scrollbar pb-2 max-w-7xl mx-auto w-full">
          {['All Items', 'Research Papers', 'News Briefs', 'Frameworks', 'Opportunities'].map((f, i) => (
            <button key={f} className={`px-4 py-1.5 rounded-full font-label text-label-md transition-colors whitespace-nowrap cursor-pointer ${i === 0 ? 'border-2 border-primary bg-primary text-on-primary' : 'border border-primary bg-surface hover:bg-surface-container-highest text-primary'}`}>{f}</button>
          ))}
        </div>
      </header>

      {/* Bento Grid */}
      <div className="p-8 flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto w-full grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 auto-rows-[280px]">
          {/* Featured */}
          <article className="xl:col-span-2 xl:row-span-2 border border-primary bg-surface-container-lowest flex flex-col relative group overflow-hidden">
            <div className="h-64 border-b border-primary relative overflow-hidden bg-surface-container-high shrink-0">
              <img alt="Research" className="w-full h-full object-cover grayscale opacity-90 group-hover:scale-105 transition-transform duration-700 ease-out" src="https://lh3.googleusercontent.com/aida-public/AB6AXuC3Nun0y51Rtx9B45OP8kMQMmkspZSbUqbUFcATDjSmnW7P9AtxmF672C3xt9PYAhtcCwMKYHf0yYu3WNMqgqQv72BWgF0JfVbFc6cxW5ei9wDhCpUNRC0cSSEBRc8bW5H0qyFMDPG74qhi4WIl1At5mefGJSxD0iBj0KHToaByL3qK0TnXyPQQMfzfmtaYg0WcZDrNenc9lT1fOsmB2mlGgU6DVMMZfSwR_4BwgKvG1FbHmCUrqoU0aeOcV4axDSclabVt1NpXjfY" />
              <div className="absolute top-4 left-4 bg-surface border border-primary px-3 py-1 font-label text-label-md uppercase tracking-wider text-primary">Priority Read</div>
            </div>
            <div className="p-6 flex-1 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-label text-label-md text-on-surface-variant flex items-center gap-2"><span className="material-symbols-outlined text-[16px]">biotech</span> Research Framework</span>
                  <span className="font-label text-label-md text-outline">Oct 24, 2023</span>
                </div>
                <h2 className="text-headline-md font-headline text-primary mb-4 leading-tight group-hover:underline decoration-2 underline-offset-4">Towards Monolithic Architecture in LLM Deployment</h2>
                <p className="text-body-lg text-on-surface-variant line-clamp-3">An exhaustive structural analysis on moving away from microservices towards a unified, rigid monolithic structure for enterprise AI agents.</p>
              </div>
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-surface-variant">
                <span className="font-label text-label-md text-primary font-bold">14 min read</span>
                <button className="text-primary hover:text-tertiary transition-colors bg-transparent border-none cursor-pointer"><span className="material-symbols-outlined icon-fill">bookmark</span></button>
              </div>
            </div>
          </article>

          {/* Standard Card */}
          <article className="border border-primary bg-surface flex flex-col group hover:bg-surface-container-lowest transition-colors">
            <div className="p-5 flex-1 flex flex-col">
              <div className="flex items-start justify-between mb-4">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 border border-outline-variant bg-surface-container text-label-md font-label text-on-surface-variant"><span className="material-symbols-outlined text-[14px]">newspaper</span> Market Intel</span>
                <button className="text-primary opacity-50 hover:opacity-100 transition-opacity bg-transparent border-none cursor-pointer"><span className="material-symbols-outlined icon-fill">bookmark</span></button>
              </div>
              <h3 className="text-2xl font-headline text-primary mb-3 leading-snug">Global Compute Allocation Shifts Q3</h3>
              <p className="text-body-md text-on-surface-variant line-clamp-4 flex-1">Data centers in the Nordic regions are experiencing a surge in structural investment, prioritizing cold-climate natural cooling for high-density training clusters.</p>
              <div className="mt-4 font-label text-label-md text-outline">Saved 2 days ago</div>
            </div>
          </article>

          {/* Data Card */}
          <article className="border border-primary bg-surface-container-highest flex flex-col group">
            <div className="p-1 border-b border-primary bg-primary text-on-primary text-center font-headline uppercase text-sm tracking-widest">Opportunity Alert</div>
            <div className="p-5 flex-1 flex flex-col justify-between">
              <div>
                <h3 className="text-xl font-headline text-primary mb-2">Defense Tech Hackathon: Autonomous Logistics</h3>
                <div className="grid grid-cols-2 gap-y-2 gap-x-4 mt-4 font-body text-body-md text-on-surface-variant border-l-2 border-primary pl-3">
                  <div><strong className="text-primary font-label text-label-md block">Location</strong> Remote / DC</div>
                  <div><strong className="text-primary font-label text-label-md block">Prize Pool</strong> $250,000</div>
                  <div><strong className="text-primary font-label text-label-md block">Deadline</strong> Nov 15</div>
                  <div><strong className="text-primary font-label text-label-md block">Team Size</strong> 2-4</div>
                </div>
              </div>
              <div className="mt-6 flex gap-2">
                <button className="flex-1 border border-primary py-2 font-label text-label-md text-primary hover:bg-surface transition-colors bg-transparent cursor-pointer">Details</button>
                <button className="w-10 flex items-center justify-center border border-primary bg-primary text-on-primary hover:bg-inverse-surface transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">open_in_new</span></button>
              </div>
            </div>
          </article>

          {/* Logs */}
          <article className="xl:col-span-2 border border-primary bg-surface flex flex-col">
            <div className="p-4 border-b border-primary flex items-center justify-between bg-surface-container-low">
              <h3 className="font-headline text-lg uppercase text-primary tracking-wide">Quick Saves &amp; Logs</h3>
              <span className="font-label text-label-md text-outline">Last 7 days</span>
            </div>
            <div className="flex-1 overflow-y-auto divide-y divide-surface-variant no-scrollbar">
              {logs.map((l) => (
                <div key={l.title} className="p-4 hover:bg-surface-container-lowest transition-colors flex items-center gap-4 group cursor-pointer">
                  <div className="w-8 h-8 rounded-full border border-outline flex items-center justify-center bg-surface shrink-0 group-hover:border-primary transition-colors">
                    <span className="material-symbols-outlined text-[16px] text-on-surface-variant group-hover:text-primary">{l.icon}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-body-md text-primary truncate font-bold">{l.title}</p>
                    <p className="text-label-md font-label text-on-surface-variant truncate">{l.desc}</p>
                  </div>
                  <button className="opacity-0 group-hover:opacity-100 transition-opacity text-outline hover:text-primary p-2 bg-transparent border-none cursor-pointer"><span className="material-symbols-outlined icon-fill">bookmark</span></button>
                </div>
              ))}
            </div>
          </article>

          {/* Quote */}
          <article className="border border-primary bg-primary text-on-primary p-6 flex flex-col justify-between group">
            <div>
              <span className="material-symbols-outlined text-4xl mb-4 text-outline-variant group-hover:text-on-primary transition-colors block">format_quote</span>
              <h3 className="text-2xl font-headline leading-tight mb-4 text-surface-container-lowest">"The architecture must dictate the flow, not the data."</h3>
              <p className="text-body-md text-inverse-primary font-body">From 'Principles of Brutalist System Design', Chapter 4.</p>
            </div>
            <div className="mt-8 pt-4 border-t border-surface-tint flex items-center justify-between">
              <span className="font-label text-label-md text-outline-variant">Note / Excerpt</span>
              <button className="text-outline-variant hover:text-on-primary transition-colors bg-transparent border-none cursor-pointer"><span className="material-symbols-outlined icon-fill">bookmark</span></button>
            </div>
          </article>
        </div>

        <div className="max-w-7xl mx-auto w-full mt-12 mb-8 pt-8 border-t border-outline flex flex-col items-center justify-center gap-4 text-on-surface-variant">
          <span className="material-symbols-outlined text-3xl opacity-50">inventory_2</span>
          <p className="font-label text-label-md uppercase tracking-widest text-center">End of Indexed Archive</p>
        </div>
      </div>
    </div>
  );
}
