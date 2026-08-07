import { useState } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { cn } from '@/utils/cn';

type TabFilter = 'upcoming' | 'ongoing' | 'completed';

const FEATURED = {
  status: 'upcoming' as TabFilter,
  title: 'Agentic Reasoning Decathlon',
  host: 'Mistral AI',
  desc: 'Build multi-agent systems capable of solving complex, multi-step logical puzzles without human intervention. Evaluation based on reasoning accuracy and execution efficiency.',
  prize: '$50,000',
  closes: 'Oct 15, 2024',
  format: 'Virtual',
  url: 'https://mistral.ai/news/',
  img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuA16Yj0lmD-H6tTliiCZmOzSOmfmLZGFEtiSS9DIAbvsa_kDDfd1m8U4NT_cC7PBf2X4kxA9xedGTMI1CCt2f_eIEz-bOEeXFIfNlKtPcEn7r-PROW_uGxHiQoPfb2Tmjx0qNaxG1El_vx6WybO--u75nexrlH6JZg7giTEPSlGDaaRo3AuQt0aNpZf2As1riZFPbIPDwVL1LeEq97sa8gbsZre_zKJGhWmzv3zDYqre5-sv4oxsykdaZJ6piI6QksLjT8X8gUbNmc',
};

const ELITE = {
  status: 'upcoming' as TabFilter,
  title: 'LLM Security & Red Teaming Challenge',
  host: 'OpenAI',
  prize: '$25,000',
  deadline: 'Nov 01, 2024',
  teamSize: '1 - 4 Members',
  url: 'https://openai.com/blog/red-teaming-network',
};

const STANDARD = [
  { status: 'upcoming' as TabFilter, icon: 'memory', cat: 'Hardware', title: 'Edge AI Optimization', host: 'Hosted by NVIDIA', prize: '4x RTX 6090', prizeLabel: 'Top Prize', closes: 'Dec 15', url: 'https://www.nvidia.com/en-us/research/' },
  { status: 'ongoing' as TabFilter, icon: 'dataset', cat: '$100k Seed', title: 'Healthcare Data Synthesizer', host: 'Hosted by DeepMind & NHS', prize: 'Privacy', prizeLabel: 'Focus', closes: 'Jan 10', url: 'https://deepmind.google/discover/blog/' },
  { status: 'upcoming' as TabFilter, icon: 'scatter_plot', cat: '$15,000', title: 'Quantum ML Algorithms', host: 'Hosted by IBM Quantum', prize: 'Qiskit Runtime', prizeLabel: 'Access', closes: 'Jan 22', url: 'https://www.ibm.com/quantum' },
];

const TABS: { value: TabFilter; label: string }[] = [
  { value: 'upcoming', label: 'Upcoming' },
  { value: 'ongoing', label: 'Ongoing' },
  { value: 'completed', label: 'Completed' },
];

export default function HackathonsPage() {
  useDocumentTitle('Hackathons — AI News Notifier');
  const [activeTab, setActiveTab] = useState<TabFilter>('upcoming');

  const filteredStandard = STANDARD.filter((s) => s.status === activeTab);
  const showFeatured = FEATURED.status === activeTab;
  const showElite = ELITE.status === activeTab;

  return (
    <div className="flex-1 p-8 lg:p-[64px]">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12 border-b border-primary pb-6">
        <div>
          <h2 className="font-bold text-[48px] leading-none text-primary">High-Stakes Arena</h2>
          <p className="font-medium text-label-md text-secondary mt-2 max-w-2xl">Discover and register for elite artificial intelligence hackathons. Precision engineering meets competitive problem-solving.</p>
        </div>
        <div className="flex gap-2 bg-surface-container-lowest border border-outline p-1 rounded-sm w-fit">
          {TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={cn(
                'px-6 py-2 font-bold text-sm rounded-sm border-none cursor-pointer transition-colors',
                activeTab === tab.value
                  ? 'bg-primary text-on-primary'
                  : 'text-on-surface-variant hover:bg-surface-container bg-transparent'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Empty state for completed */}
      {!showFeatured && !showElite && filteredStandard.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="material-symbols-outlined text-6xl text-on-surface-variant mb-4">emoji_events</span>
          <h3 className="text-xl font-bold text-on-surface mb-2">No {activeTab} hackathons</h3>
          <p className="text-on-surface-variant font-body text-sm max-w-xs">
            {activeTab === 'completed' ? 'Completed hackathons will appear here.' : 'Check back soon for new events.'}
          </p>
        </div>
      )}

      {/* Bento Grid */}
      {(showFeatured || showElite || filteredStandard.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 auto-rows-[minmax(300px,auto)]">
          {/* Highlight Card */}
          {showFeatured && (
            <article
              onClick={() => window.open(FEATURED.url, '_blank')}
              className="md:col-span-8 bg-surface-container-lowest border border-primary flex flex-col group relative overflow-hidden rounded cursor-pointer"
            >
              <div className="h-64 border-b border-primary relative overflow-hidden bg-surface-container-highest">
                <img className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity duration-500 mix-blend-luminosity" alt="Hackathon visual" src={FEATURED.img} />
                <div className="absolute top-4 left-4 bg-primary text-on-primary px-3 py-1 font-bold text-xs border border-primary">Featured</div>
              </div>
              <div className="p-8 flex flex-col flex-1 justify-between bg-surface-container-lowest">
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-[32px] text-primary leading-tight group-hover:underline">{FEATURED.title}</h3>
                    <span className="font-bold text-[24px] text-primary bg-surface-container px-3 py-1 border border-outline">{FEATURED.prize}</span>
                  </div>
                  <p className="font-medium text-on-surface-variant text-sm flex items-center gap-2 mb-6">
                    <span className="material-symbols-outlined text-[16px]">corporate_fare</span> Hosted by {FEATURED.host}
                  </p>
                  <p className="font-body text-body-lg text-on-surface mb-8 max-w-xl">{FEATURED.desc}</p>
                </div>
                <div className="flex items-center justify-between border-t border-outline pt-6">
                  <div className="flex items-center gap-6">
                    <div className="flex flex-col"><span className="font-medium text-xs text-secondary">Registration Closes</span><span className="font-bold text-lg text-primary">{FEATURED.closes}</span></div>
                    <div className="w-px h-10 bg-outline" />
                    <div className="flex flex-col"><span className="font-medium text-xs text-secondary">Format</span><span className="font-bold text-lg text-primary">{FEATURED.format}</span></div>
                  </div>
                </div>
              </div>
            </article>
          )}

          {/* Elite Card */}
          {showElite && (
            <article
              onClick={() => window.open(ELITE.url, '_blank')}
              className="md:col-span-4 bg-primary text-on-primary border border-primary flex flex-col rounded p-6 relative overflow-hidden cursor-pointer group"
            >
              <div className="absolute inset-0 opacity-10 pointer-events-none" style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '16px 16px' }} />
              <div className="flex-1 z-10 flex flex-col">
                <div className="mb-auto">
                  <div className="inline-block bg-surface text-primary px-2 py-1 font-bold text-xs mb-6">Elite Tier</div>
                  <h3 className="font-bold text-[28px] leading-tight mb-2 group-hover:underline">{ELITE.title}</h3>
                  <p className="font-medium text-inverse-primary text-sm mb-6 border-b border-surface-tint pb-4">Hosted by {ELITE.host}</p>
                </div>
                <div className="bg-surface-tint/30 border border-surface-tint p-4 rounded mb-6 backdrop-blur-sm">
                  <span className="font-medium text-xs text-inverse-primary block mb-1">Prize Pool</span>
                  <span className="font-bold text-[32px] block leading-none">{ELITE.prize}</span>
                </div>
                <div className="flex flex-col gap-4">
                  <div className="flex justify-between items-center font-medium text-sm border-b border-surface-tint pb-2"><span className="uppercase text-inverse-primary">Deadline</span><span>{ELITE.deadline}</span></div>
                  <div className="flex justify-between items-center font-medium text-sm border-b border-surface-tint pb-2"><span className="uppercase text-inverse-primary">Team Size</span><span>{ELITE.teamSize}</span></div>
                </div>
              </div>
            </article>
          )}

          {/* Standard Cards */}
          {filteredStandard.map((s) => (
            <article
              key={s.title}
              onClick={() => window.open(s.url, '_blank')}
              className="md:col-span-4 bg-surface-container-lowest border border-outline flex flex-col p-6 rounded hover:border-primary transition-colors group cursor-pointer"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="w-12 h-12 bg-surface-container flex items-center justify-center rounded border border-outline-variant group-hover:bg-primary group-hover:text-on-primary transition-colors">
                  <span className="material-symbols-outlined">{s.icon}</span>
                </div>
                <span className="font-bold text-lg text-primary bg-surface px-2 py-1 border border-outline-variant rounded-sm group-hover:border-primary transition-colors">{s.cat}</span>
              </div>
              <h3 className="font-bold text-[24px] text-primary leading-tight mb-1 group-hover:underline">{s.title}</h3>
              <p className="font-medium text-secondary text-xs mb-4">{s.host}</p>
              <div className="mt-auto pt-6 border-t border-outline-variant flex justify-between items-end">
                <div><span className="font-medium text-xs text-secondary block">{s.prizeLabel}</span><span className="font-bold text-primary text-xl">{s.prize}</span></div>
                <div className="text-right"><span className="font-medium text-xs text-secondary block">Closes</span><span className="font-body text-primary font-bold">{s.closes}</span></div>
              </div>
            </article>
          ))}
        </div>
      )}
      <div className="h-24" />
    </div>
  );
}
