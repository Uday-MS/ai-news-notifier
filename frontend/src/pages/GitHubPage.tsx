import { useDocumentTitle } from '@/hooks/useDocumentTitle';

export default function GitHubPage() {
  useDocumentTitle('GitHub Trending — Platinum Mist');

  const repos = [
    { name: 'ggerganov / llama.cpp', desc: "Port of Facebook's LLaMA model in C/C++. Inference of LLaMA model in pure C/C++.", lang: 'C++', stars: '52k' },
    { name: 'chroma-core / chroma', desc: 'the open source AI native vector database. Chroma makes it easy to build AI apps.', lang: 'Python', stars: '11k' },
    { name: 'hwchase17 / langchain', desc: 'Building applications with LLMs through composability. Orchestration framework.', lang: 'Python', stars: '78k' },
  ];

  return (
    <div className="p-8 lg:p-12 max-w-7xl mx-auto w-full">
      <div className="mb-12 border-b-2 border-primary pb-6 flex justify-between items-end">
        <div>
          <h1 className="text-6xl font-headline uppercase tracking-tight text-primary">Trending Repositories</h1>
          <p className="text-body-lg text-on-surface-variant mt-2 max-w-2xl">High-impact artificial intelligence projects gaining traction in the developer community.</p>
        </div>
        <div className="flex gap-4">
          <select className="bg-surface-container border border-outline rounded text-label-md font-label py-2 px-4 focus:ring-primary focus:border-primary">
            <option>Language: Any</option><option>Python</option><option>Rust</option><option>C++</option>
          </select>
          <select className="bg-surface-container border border-outline rounded text-label-md font-label py-2 px-4 focus:ring-primary focus:border-primary">
            <option>Date Range: Today</option><option>This Week</option><option>This Month</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Featured Repo */}
        <div className="md:col-span-2 border border-primary bg-surface p-6 rounded-lg flex flex-col justify-between hover:bg-surface-container-low transition-colors group relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <span className="material-symbols-outlined text-9xl">memory</span>
          </div>
          <div>
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-3xl font-headline text-primary uppercase">mistralai / mistral-src</h3>
              <div className="flex items-center gap-2 bg-surface-container-high px-3 py-1 rounded-full text-label-md font-label">
                <span className="material-symbols-outlined text-sm">star</span><span>34,210</span>
              </div>
            </div>
            <p className="text-body-lg text-on-surface-variant mb-6 relative z-10 w-4/5">Reference implementation of Mistral AI 7B v0.1 model. Highly efficient, open-weight language model demonstrating superior performance metrics across benchmarks.</p>
            <div className="flex gap-2 mb-6">
              {['Python', 'LLM', 'Transformers'].map((t) => <span key={t} className="bg-surface-container px-3 py-1 rounded text-label-md font-label border border-outline-variant">{t}</span>)}
            </div>
          </div>
          <div className="flex justify-between items-center border-t border-outline-variant pt-4 relative z-10">
            <div className="flex items-center gap-2">
              <img className="w-8 h-8 rounded-full border border-primary grayscale" alt="Mistral AI" src="https://lh3.googleusercontent.com/aida-public/AB6AXuATVP-Wf-H7VvImDsDpp-yzqW35sZlcKAuCnqHMPGa-_WCciQ1xE173aqWxs_jy4V7wjn7DPBIHTpFswPqF2jA5tk0Rfy12ylfK1OK_k3tMjl9_Oci9ZEL-3lw2DkmTeRy2nnOPLZqLin6ZQdN-jNZ3cu07yjnWrwshajS_pu75vHB8lZHFAr0pRJQ5YXEfI7-7_Z-nChuOyYr_dYaCE7AHTF5gdAdxz8A5s1IIT00TL35pcjSKy9PNmCIVIR24vCYc1-afd-JX7nw" />
              <span className="text-label-md font-label font-semibold">Built by Mistral AI</span>
            </div>
            <button className="flex items-center gap-2 text-primary font-bold hover:underline font-label bg-transparent border-none cursor-pointer">View Repository <span className="material-symbols-outlined">arrow_forward</span></button>
          </div>
        </div>

        {/* Mist Analysis */}
        <div className="border border-primary bg-primary text-on-primary p-6 rounded-lg flex flex-col justify-between">
          <div>
            <h4 className="text-xl font-headline uppercase tracking-widest mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined">troubleshoot</span> Mist Analysis
            </h4>
            <p className="text-body-md text-on-primary-container mb-4">Our AI indicates a 45% surge in fork activity on local-LLM repositories over the past 72 hours, correlating with new edge-compute hardware announcements.</p>
            <div className="space-y-3">
              <div className="bg-primary-container p-3 rounded border border-outline-variant/30">
                <div className="text-label-md font-label text-on-primary-container mb-1">Momentum Score</div>
                <div className="flex items-end gap-2"><span className="text-2xl font-headline">94.2</span><span className="text-label-md text-tertiary-fixed-dim">/ 100</span></div>
              </div>
              <div className="bg-primary-container p-3 rounded border border-outline-variant/30">
                <div className="text-label-md font-label text-on-primary-container mb-1">Dominant Language</div>
                <div className="text-xl font-headline">RUST <span className="text-sm font-body text-on-primary-container">+12%</span></div>
              </div>
            </div>
          </div>
        </div>

        {/* Standard Repos */}
        {repos.map((r) => (
          <div key={r.name} className="border border-outline bg-surface p-6 rounded-lg hover:border-primary transition-colors flex flex-col">
            <h3 className="text-xl font-headline text-primary uppercase mb-2 truncate">{r.name}</h3>
            <p className="text-body-md text-on-surface-variant flex-grow mb-4">{r.desc}</p>
            <div className="flex justify-between items-center mt-auto">
              <span className="text-label-md font-label text-secondary flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-secondary inline-block" /> {r.lang}</span>
              <div className="flex items-center gap-1 text-label-md font-label"><span className="material-symbols-outlined text-sm">star</span> {r.stars}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12 text-center">
        <button className="border-2 border-primary text-primary font-headline uppercase px-8 py-3 rounded hover:bg-primary hover:text-on-primary transition-colors tracking-widest inline-flex items-center gap-2 bg-transparent cursor-pointer">
          Load More Data <span className="material-symbols-outlined">expand_more</span>
        </button>
      </div>
    </div>
  );
}
