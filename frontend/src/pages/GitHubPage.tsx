import { useState } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';

const ALL_REPOS = [
  { name: 'ggerganov / llama.cpp', desc: "Port of Facebook's LLaMA model in C/C++. Inference of LLaMA model in pure C/C++.", lang: 'C++', stars: '52k', url: 'https://github.com/ggerganov/llama.cpp' },
  { name: 'chroma-core / chroma', desc: 'the open source AI native vector database. Chroma makes it easy to build AI apps.', lang: 'Python', stars: '11k', url: 'https://github.com/chroma-core/chroma' },
  { name: 'hwchase17 / langchain', desc: 'Building applications with LLMs through composability. Orchestration framework.', lang: 'Python', stars: '78k', url: 'https://github.com/langchain-ai/langchain' },
  { name: 'huggingface / transformers', desc: 'State-of-the-art Machine Learning for PyTorch, TensorFlow, and JAX.', lang: 'Python', stars: '120k', url: 'https://github.com/huggingface/transformers' },
  { name: 'openai / whisper', desc: 'Robust Speech Recognition via Large-Scale Weak Supervision.', lang: 'Python', stars: '58k', url: 'https://github.com/openai/whisper' },
  { name: 'rustformers / llm', desc: 'Run inference for Large Language Models on CPU, with Rust.', lang: 'Rust', stars: '6.2k', url: 'https://github.com/rustformers/llm' },
];

const FEATURED = {
  name: 'mistralai / mistral-src',
  desc: 'Reference implementation of Mistral AI 7B v0.1 model. Highly efficient, open-weight language model demonstrating superior performance metrics across benchmarks.',
  stars: '34,210',
  tags: ['Python', 'LLM', 'Transformers'],
  url: 'https://github.com/mistralai/mistral-inference',
};

const LANGUAGES = ['Any', 'Python', 'Rust', 'C++'];

export default function GitHubPage() {
  useDocumentTitle('GitHub Trending — AI News Notifier');
  const [langFilter, setLangFilter] = useState('Any');
  const [showAll, setShowAll] = useState(false);

  const filtered = langFilter === 'Any'
    ? ALL_REPOS
    : ALL_REPOS.filter((r) => r.lang === langFilter);

  const displayed = showAll ? filtered : filtered.slice(0, 3);

  return (
    <div className="p-8 lg:p-12 max-w-7xl mx-auto w-full">
      <div className="mb-12 border-b-2 border-primary pb-6 flex justify-between items-end">
        <div>
          <h1 className="text-6xl font-bold tracking-tight text-primary">Trending Repositories</h1>
          <p className="text-body-lg text-on-surface-variant mt-2 max-w-2xl">High-impact artificial intelligence projects gaining traction in the developer community.</p>
        </div>
        <div className="flex gap-4">
          <select
            value={langFilter}
            onChange={(e) => { setLangFilter(e.target.value); setShowAll(false); }}
            className="bg-surface-container border border-outline rounded text-label-md font-medium py-2 px-4 focus:ring-primary focus:border-primary"
          >
            {LANGUAGES.map((l) => (
              <option key={l} value={l}>Language: {l}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Featured Repo */}
        <div
          onClick={() => window.open(FEATURED.url, '_blank')}
          className="md:col-span-2 border border-primary bg-surface p-6 rounded-lg flex flex-col justify-between hover:bg-surface-container-low transition-colors group relative overflow-hidden cursor-pointer"
        >
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <span className="material-symbols-outlined text-9xl">memory</span>
          </div>
          <div>
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-3xl font-bold text-primary">{FEATURED.name}</h3>
              <div className="flex items-center gap-2 bg-surface-container-high px-3 py-1 rounded-full text-label-md font-medium">
                <span className="material-symbols-outlined text-sm">star</span><span>{FEATURED.stars}</span>
              </div>
            </div>
            <p className="text-body-lg text-on-surface-variant mb-6 relative z-10 w-4/5">{FEATURED.desc}</p>
            <div className="flex gap-2 mb-6">
              {FEATURED.tags.map((t) => <span key={t} className="bg-surface-container px-3 py-1 rounded text-label-md font-medium border border-outline-variant">{t}</span>)}
            </div>
          </div>
          <div className="flex justify-between items-center border-t border-outline-variant pt-4 relative z-10">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary text-on-primary flex items-center justify-center font-bold text-sm">M</div>
              <span className="text-label-md font-medium font-semibold">Built by Mistral AI</span>
            </div>
            <span className="flex items-center gap-2 text-primary font-bold font-medium">
              View Repository <span className="material-symbols-outlined">arrow_forward</span>
            </span>
          </div>
        </div>

        {/* Analysis */}
        <div className="border border-primary bg-primary text-on-primary p-6 rounded-lg flex flex-col justify-between">
          <div>
            <h4 className="text-xl font-bold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined">troubleshoot</span> Trend Analysis
            </h4>
            <p className="text-body-md text-on-primary-container mb-4">Our AI indicates a 45% surge in fork activity on local-LLM repositories over the past 72 hours, correlating with new edge-compute hardware announcements.</p>
            <div className="space-y-3">
              <div className="bg-primary-container p-3 rounded border border-outline-variant/30">
                <div className="text-label-md font-medium text-on-primary-container mb-1">Momentum Score</div>
                <div className="flex items-end gap-2"><span className="text-2xl font-bold">94.2</span><span className="text-label-md text-tertiary-fixed-dim">/ 100</span></div>
              </div>
              <div className="bg-primary-container p-3 rounded border border-outline-variant/30">
                <div className="text-label-md font-medium text-on-primary-container mb-1">Dominant Language</div>
                <div className="text-xl font-bold">RUST <span className="text-sm font-body text-on-primary-container">+12%</span></div>
              </div>
            </div>
          </div>
        </div>

        {/* Standard Repos */}
        {displayed.map((r) => (
          <div
            key={r.name}
            onClick={() => window.open(r.url, '_blank')}
            className="border border-outline bg-surface p-6 rounded-lg hover:border-primary transition-colors flex flex-col cursor-pointer group"
          >
            <h3 className="text-xl font-bold text-primary mb-2 truncate group-hover:underline">{r.name}</h3>
            <p className="text-body-md text-on-surface-variant flex-grow mb-4">{r.desc}</p>
            <div className="flex justify-between items-center mt-auto">
              <span className="text-label-md font-medium text-secondary flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-secondary inline-block" /> {r.lang}</span>
              <div className="flex items-center gap-1 text-label-md font-medium"><span className="material-symbols-outlined text-sm">star</span> {r.stars}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Load More */}
      {!showAll && filtered.length > 3 && (
        <div className="mt-12 text-center">
          <button
            onClick={() => setShowAll(true)}
            className="border-2 border-primary text-primary font-bold px-8 py-3 rounded hover:bg-primary hover:text-on-primary transition-colors inline-flex items-center gap-2 bg-transparent cursor-pointer"
          >
            Load More Data <span className="material-symbols-outlined">expand_more</span>
          </button>
        </div>
      )}
      {showAll && (
        <div className="mt-12 text-center">
          <p className="text-on-surface-variant font-body text-sm">All repositories loaded.</p>
        </div>
      )}
    </div>
  );
}
