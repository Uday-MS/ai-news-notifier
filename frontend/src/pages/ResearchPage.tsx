import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';

const FEATURED = {
  id: '2405.01234',
  title: 'Emergent Reasoning Protocols in Large Language Models',
  summary: 'An exhaustive analysis of multi-step inference capabilities in models exceeding 100B parameters, demonstrating spontaneous protocol generation without explicit few-shot prompting.',
  tags: ['Reasoning', 'LLM Architecture'],
  relevance: 98,
  url: 'https://arxiv.org/abs/2405.01234',
};

const CITATIONS = [
  { rank: '01', title: 'Attention Mechanisms in Vision Models', src: 'NATURE AI • +450 citations/wk', w: '85%', url: 'https://scholar.google.com/scholar?q=attention+mechanisms+vision+models' },
  { rank: '02', title: 'Quantum-Assisted Neural Training', src: 'IEEE Xplore • +320 citations/wk', w: '65%', url: 'https://scholar.google.com/scholar?q=quantum+assisted+neural+training' },
  { rank: '03', title: 'Neuromorphic Hardware Benchmarks', src: 'ARXIV • +290 citations/wk', w: '50%', url: 'https://scholar.google.com/scholar?q=neuromorphic+hardware+benchmarks' },
];

const CURATED = [
  { cat: 'Hardware', title: 'Scaling Laws for Silicon-Photonic Neural Chips', desc: 'A critical review of power consumption metrics as optical computing intersects with traditional von Neumann architectures.', author: 'Chen, et al.', views: '12.4k', url: 'https://arxiv.org/search/?query=silicon+photonic+neural&searchtype=all' },
  { cat: 'Ethics / Policy', title: 'Algorithmic Bias in Predictive Policing Models', desc: 'Meta-analysis revealing systemic failure points in demographic weighting across five major deployment jurisdictions.', author: 'Davis, M.', views: '8.9k', url: 'https://arxiv.org/search/?query=algorithmic+bias+policing&searchtype=all' },
  { cat: 'Algorithms', title: 'Optimizing Sparse Attention via Graph Theory', desc: 'Proposing a novel mapping technique that reduces memory footprint by 40% without sacrificing perplexity scores.', author: 'Kumar & Lin', views: '15.1k', url: 'https://arxiv.org/search/?query=sparse+attention+graph+theory&searchtype=all' },
];

export default function ResearchPage() {
  useDocumentTitle('Research — AI News Notifier');
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/news?q=${encodeURIComponent(searchQuery.trim())}&category=ai_research`);
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto w-full">
      {/* Search */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="relative">
          <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant">search</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search research papers..."
            className="w-full py-3 pl-12 pr-4 bg-surface-container border border-outline text-body-md font-body text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors rounded"
          />
        </div>
      </form>

      {/* Hero Section */}
      <section className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-12">
        {/* Featured Article */}
        <article
          onClick={() => window.open(FEATURED.url, '_blank')}
          className="md:col-span-8 bg-surface-container-lowest border-2 border-primary rounded-lg overflow-hidden flex flex-col group relative cursor-pointer"
        >
          <div className="p-6 border-b border-primary flex justify-between items-center bg-surface-container">
            <span className="text-label-md font-label text-primary uppercase tracking-widest font-bold">BREAKING RESEARCH // ARXIV</span>
            <span className="text-label-md font-label text-on-surface-variant">ID: {FEATURED.id}</span>
          </div>
          <div className="flex-1 p-8 flex flex-col justify-center">
            <h2 className="text-headline-lg font-headline text-primary mb-6 leading-none group-hover:text-surface-tint transition-colors">{FEATURED.title}</h2>
            <p className="text-body-lg text-on-surface-variant mb-8 max-w-2xl border-l-4 border-primary pl-4">{FEATURED.summary}</p>
            <div className="flex flex-wrap gap-3 mt-auto">
              {FEATURED.tags.map((t) => (
                <span key={t} className="px-3 py-1 bg-surface-container-high text-on-surface-variant text-label-md font-label rounded-full border border-outline-variant">{t}</span>
              ))}
              <span className="px-3 py-1 bg-primary text-on-primary text-label-md font-label rounded-full border border-primary font-bold">{FEATURED.relevance}% Relevance</span>
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
            {CITATIONS.map((item, i) => (
              <div
                key={item.rank}
                onClick={() => window.open(item.url, '_blank')}
                className={`flex items-start gap-4 cursor-pointer hover:opacity-80 transition-opacity ${i < 2 ? 'pb-4 border-b border-surface-tint' : ''}`}
              >
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
        <button
          onClick={() => navigate('/news?category=ai_research')}
          className="text-label-md font-label font-bold text-primary hover:underline flex items-center gap-1 bg-transparent border-none cursor-pointer"
        >
          View Full Corpus <span className="material-symbols-outlined text-sm">arrow_forward</span>
        </button>
      </div>
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {CURATED.map((card) => (
          <div
            key={card.title}
            onClick={() => window.open(card.url, '_blank')}
            className="bg-surface-container-lowest border border-outline hover:border-primary transition-colors flex flex-col h-full rounded-md shadow-sm cursor-pointer group"
          >
            <div className="h-48 border-b border-outline relative overflow-hidden bg-surface-container-highest">
              <div className="absolute inset-0 bg-primary/10 flex items-center justify-center">
                <span className="material-symbols-outlined text-6xl text-primary/30 group-hover:scale-110 transition-transform">description</span>
              </div>
              <div className="absolute top-4 left-4 bg-primary text-on-primary text-xs font-label uppercase px-2 py-1 font-bold">{card.cat}</div>
            </div>
            <div className="p-5 flex flex-col flex-1">
              <h4 className="text-body-lg font-bold text-on-surface mb-2 leading-snug group-hover:text-primary transition-colors">{card.title}</h4>
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
