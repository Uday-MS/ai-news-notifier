import { useDocumentTitle } from '@/hooks/useDocumentTitle';

export default function ResearchPage() {
  useDocumentTitle('Research — Platinum Mist');

  return (
    <div className="p-8 max-w-7xl mx-auto w-full">
      {/* Hero Section */}
      <section className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-12">
        {/* Featured Article */}
        <article className="md:col-span-8 bg-surface-container-lowest border-2 border-primary rounded-lg overflow-hidden flex flex-col group relative">
          <div className="p-6 border-b border-primary flex justify-between items-center bg-surface-container">
            <span className="text-label-md font-label text-primary uppercase tracking-widest font-bold">BREAKING RESEARCH // ARXIV</span>
            <span className="text-label-md font-label text-on-surface-variant">ID: 2405.01234</span>
          </div>
          <div className="flex-1 p-8 flex flex-col justify-center">
            <h2 className="text-headline-lg font-headline text-primary mb-6 leading-none group-hover:text-surface-tint transition-colors">Emergent Reasoning Protocols in Large Language Models</h2>
            <p className="text-body-lg text-on-surface-variant mb-8 max-w-2xl border-l-4 border-primary pl-4">An exhaustive analysis of multi-step inference capabilities in models exceeding 100B parameters, demonstrating spontaneous protocol generation without explicit few-shot prompting.</p>
            <div className="flex flex-wrap gap-3 mt-auto">
              <span className="px-3 py-1 bg-surface-container-high text-on-surface-variant text-label-md font-label rounded-full border border-outline-variant">Reasoning</span>
              <span className="px-3 py-1 bg-surface-container-high text-on-surface-variant text-label-md font-label rounded-full border border-outline-variant">LLM Architecture</span>
              <span className="px-3 py-1 bg-primary text-on-primary text-label-md font-label rounded-full border border-primary font-bold">98% Relevance</span>
            </div>
          </div>
          <div className="absolute bottom-0 right-0 w-1/3 h-full opacity-5 pointer-events-none" style={{ backgroundImage: 'repeating-linear-gradient(45deg, #16191e 0, #16191e 2px, transparent 2px, transparent 8px)' }} />
        </article>

        {/* Citation Velocity */}
        <aside className="md:col-span-4 bg-primary text-on-primary rounded-lg flex flex-col border border-primary overflow-hidden">
          <div className="p-4 border-b border-surface-tint bg-primary-container flex items-center justify-between">
            <span className="text-label-md font-label uppercase tracking-widest font-bold text-on-primary-container">Citation Velocity</span>
            <span className="material-symbols-outlined text-on-primary-container">trending_up</span>
          </div>
          <div className="p-6 flex-1 flex flex-col gap-6">
            {[
              { rank: '01', title: 'Attention Mechanisms in Vision Models', src: 'NATURE AI • +450 citations/wk', w: '85%' },
              { rank: '02', title: 'Quantum-Assisted Neural Training', src: 'IEEE Xplore • +320 citations/wk', w: '65%' },
              { rank: '03', title: 'Neuromorphic Hardware Benchmarks', src: 'ARXIV • +290 citations/wk', w: '50%' },
            ].map((item, i) => (
              <div key={item.rank} className={`flex items-start gap-4 ${i < 2 ? 'pb-4 border-b border-surface-tint' : ''}`}>
                <span className="text-headline-md font-headline text-surface-dim">{item.rank}</span>
                <div>
                  <h4 className="text-body-lg font-bold leading-tight mb-1">{item.title}</h4>
                  <span className="text-label-md font-label text-inverse-on-surface block mb-2">{item.src}</span>
                  <div className="w-full bg-surface-tint h-1 mt-2"><div className="bg-on-primary h-1" style={{ width: item.w }} /></div>
                </div>
              </div>
            ))}
          </div>
        </aside>
      </section>

      {/* Curated Intelligence */}
      <div className="flex items-center justify-between mb-6 border-b-2 border-primary pb-2">
        <h3 className="text-headline-md font-headline text-primary uppercase">Curated Intelligence</h3>
        <button className="text-label-md font-label font-bold text-primary hover:underline flex items-center gap-1 bg-transparent border-none cursor-pointer">View Full Corpus <span className="material-symbols-outlined text-sm">arrow_forward</span></button>
      </div>
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { cat: 'Hardware', title: 'Scaling Laws for Silicon-Photonic Neural Chips', desc: 'A critical review of power consumption metrics as optical computing intersects with traditional von Neumann architectures.', author: 'Chen, et al.', views: '12.4k', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAy4uhjYgQorWbBo3r228NqM5B2ciwFHoQV0TXmboYYG5NfuARHUYkMCBdGGlzouSaNpelYkFwl04FauMSJy73NDqRtTjmVJmLpkXyMHenBMA0qZq5jUxK5q80H-ERrhgmC1XDI449_3xNeG9fjHCWnTBGh8zfm-PFBbQXuEtwCU2ueXS_ChGWV-Mkp15tZ_0q5qEP1kjUuRKwmVyLqoAG9DnZkOsm8rKMqlQZvMcjVUwGlPICuKZem_fvscY3Cyku0-yIqLn8_2hU' },
          { cat: 'Ethics / Policy', title: 'Algorithmic Bias in Predictive Policing Models', desc: 'Meta-analysis revealing systemic failure points in demographic weighting across five major deployment jurisdictions.', author: 'Davis, M.', views: '8.9k', icon: 'data_object' },
          { cat: 'Algorithms', title: 'Optimizing Sparse Attention via Graph Theory', desc: 'Proposing a novel mapping technique that reduces memory footprint by 40% without sacrificing perplexity scores.', author: 'Kumar & Lin', views: '15.1k', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC-j5813IjIRW4SYwWUoUzfsMTBorzx6yM7V67QBk2H1RbmonjCaETDdKPUvdnEbeVZCFu8JexIoZqJaduMaUzc4hhrlV_PD9GBFUmryi5cRlI65FJYkfD2X1VpQN24WvJK3lerEcuz09EkHoHUrBnkhrYhCL9T2yAxb3wYYTgUPk2cbawZ2u5urixzEc2GuB2dVW9FSjqNRzlX6bcm6R62wYrF0ehA47W-GG6LZO40sbxhocOl5vNDhPzGR4G8xaH7MFFeWZRVG5k' },
        ].map((card) => (
          <div key={card.title} className="bg-surface-container-lowest border border-outline hover:border-primary transition-colors flex flex-col h-full rounded-md shadow-sm">
            <div className="h-48 border-b border-outline relative overflow-hidden bg-surface-container-highest">
              {card.img ? (
                <div className="absolute inset-0 bg-cover bg-center grayscale mix-blend-multiply opacity-80" style={{ backgroundImage: `url('${card.img}')` }} />
              ) : (
                <div className="absolute inset-0 bg-primary flex items-center justify-center">
                  <span className="material-symbols-outlined text-6xl text-surface-tint opacity-50">{card.icon}</span>
                </div>
              )}
              <div className={`absolute top-4 left-4 ${card.icon ? 'bg-surface text-primary border border-primary' : 'bg-primary text-on-primary'} text-xs font-label uppercase px-2 py-1 font-bold`}>{card.cat}</div>
            </div>
            <div className="p-5 flex flex-col flex-1">
              <h4 className="text-body-lg font-bold text-on-surface mb-2 leading-snug">{card.title}</h4>
              <p className="text-body-md text-on-surface-variant line-clamp-3 mb-4">{card.desc}</p>
              <div className="mt-auto flex justify-between items-center text-label-md font-label text-on-surface-variant pt-4 border-t border-surface-container-high">
                <span>Author: {card.author}</span>
                <span className="flex items-center gap-1"><span className="material-symbols-outlined text-sm">visibility</span> {card.views}</span>
              </div>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
