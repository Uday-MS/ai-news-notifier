import { useDocumentTitle } from '@/hooks/useDocumentTitle';

export default function HackathonsPage() {
  useDocumentTitle('Hackathons — Platinum Mist');

  const standard = [
    { icon: 'memory', cat: 'Hardware', title: 'Edge AI Optimization', host: 'Hosted by NVIDIA', prize: '4x RTX 6090', prizeLabel: 'Top Prize', closes: 'Dec 15' },
    { icon: 'dataset', cat: '$100k Seed', title: 'Healthcare Data Synthesizer', host: 'Hosted by DeepMind & NHS', prize: 'Privacy', prizeLabel: 'Focus', closes: 'Jan 10' },
    { icon: 'scatter_plot', cat: '$15,000', title: 'Quantum ML Algorithms', host: 'Hosted by IBM Quantum', prize: 'Qiskit Runtime', prizeLabel: 'Access', closes: 'Jan 22' },
  ];

  return (
    <div className="flex-1 p-8 lg:p-[64px]">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12 border-b border-primary pb-6">
        <div>
          <h2 className="font-headline text-[48px] leading-none text-primary uppercase tracking-wide">High-Stakes Arena</h2>
          <p className="font-label text-label-md text-secondary mt-2 max-w-2xl">Discover and register for elite artificial intelligence hackathons. Precision engineering meets competitive problem-solving.</p>
        </div>
        <div className="flex gap-2 bg-surface-container-lowest border border-outline p-1 rounded-sm w-fit">
          <button className="px-6 py-2 bg-primary text-on-primary font-headline uppercase text-sm tracking-wider rounded-sm border-none cursor-pointer">Upcoming</button>
          <button className="px-6 py-2 text-on-surface-variant hover:bg-surface-container font-headline uppercase text-sm tracking-wider rounded-sm transition-colors bg-transparent border-none cursor-pointer">Ongoing</button>
          <button className="px-6 py-2 text-on-surface-variant hover:bg-surface-container font-headline uppercase text-sm tracking-wider rounded-sm transition-colors bg-transparent border-none cursor-pointer">Completed</button>
        </div>
      </div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 auto-rows-[minmax(300px,auto)]">
        {/* Highlight Card */}
        <article className="md:col-span-8 bg-surface-container-lowest border border-primary flex flex-col group relative overflow-hidden rounded">
          <div className="h-64 border-b border-primary relative overflow-hidden bg-surface-container-highest">
            <img className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity duration-500 mix-blend-luminosity" alt="Hackathon visual" src="https://lh3.googleusercontent.com/aida-public/AB6AXuA16Yj0lmD-H6tTliiCZmOzSOmfmLZGFEtiSS9DIAbvsa_kDDfd1m8U4NT_cC7PBf2X4kxA9xedGTMI1CCt2f_eIEz-bOEeXFIfNlKtPcEn7r-PROW_uGxHiQoPfb2Tmjx0qNaxG1El_vx6WybO--u75nexrlH6JZg7giTEPSlGDaaRo3AuQt0aNpZf2As1riZFPbIPDwVL1LeEq97sa8gbsZre_zKJGhWmzv3zDYqre5-sv4oxsykdaZJ6piI6QksLjT8X8gUbNmc" />
            <div className="absolute top-4 left-4 bg-primary text-on-primary px-3 py-1 font-headline uppercase text-xs tracking-widest border border-primary">Featured</div>
          </div>
          <div className="p-8 flex flex-col flex-1 justify-between bg-surface-container-lowest">
            <div>
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-headline text-[32px] text-primary leading-tight uppercase">Agentic Reasoning Decathlon</h3>
                <span className="font-headline text-[24px] text-primary bg-surface-container px-3 py-1 border border-outline">$50,000</span>
              </div>
              <p className="font-label text-on-surface-variant uppercase text-sm flex items-center gap-2 mb-6">
                <span className="material-symbols-outlined text-[16px]">corporate_fare</span> Hosted by Mistral AI
              </p>
              <p className="font-body text-body-lg text-on-surface mb-8 max-w-xl">Build multi-agent systems capable of solving complex, multi-step logical puzzles without human intervention. Evaluation based on reasoning accuracy and execution efficiency.</p>
            </div>
            <div className="flex items-center justify-between border-t border-outline pt-6">
              <div className="flex items-center gap-6">
                <div className="flex flex-col"><span className="font-label text-xs uppercase text-secondary">Registration Closes</span><span className="font-headline text-lg text-primary uppercase">Oct 15, 2024</span></div>
                <div className="w-px h-10 bg-outline" />
                <div className="flex flex-col"><span className="font-label text-xs uppercase text-secondary">Format</span><span className="font-headline text-lg text-primary uppercase">Virtual</span></div>
              </div>
            </div>
          </div>
        </article>

        {/* Elite Card */}
        <article className="md:col-span-4 bg-primary text-on-primary border border-primary flex flex-col rounded p-6 relative overflow-hidden">
          <div className="absolute inset-0 opacity-10 pointer-events-none" style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '16px 16px' }} />
          <div className="flex-1 z-10 flex flex-col">
            <div className="mb-auto">
              <div className="inline-block bg-surface text-primary px-2 py-1 font-headline uppercase text-xs tracking-widest mb-6">Elite Tier</div>
              <h3 className="font-headline text-[28px] leading-tight uppercase mb-2">LLM Security &amp; Red Teaming Challenge</h3>
              <p className="font-label text-inverse-primary uppercase text-sm mb-6 border-b border-surface-tint pb-4">Hosted by OpenAI</p>
            </div>
            <div className="bg-surface-tint/30 border border-surface-tint p-4 rounded mb-6 backdrop-blur-sm">
              <span className="font-label text-xs uppercase text-inverse-primary block mb-1">Prize Pool</span>
              <span className="font-headline text-[32px] block leading-none">$25,000</span>
            </div>
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-center font-label text-sm border-b border-surface-tint pb-2"><span className="uppercase text-inverse-primary">Deadline</span><span>Nov 01, 2024</span></div>
              <div className="flex justify-between items-center font-label text-sm border-b border-surface-tint pb-2"><span className="uppercase text-inverse-primary">Team Size</span><span>1 - 4 Members</span></div>
            </div>
          </div>
        </article>

        {/* Standard Cards */}
        {standard.map((s) => (
          <article key={s.title} className="md:col-span-4 bg-surface-container-lowest border border-outline flex flex-col p-6 rounded hover:border-primary transition-colors group cursor-pointer">
            <div className="flex justify-between items-start mb-4">
              <div className="w-12 h-12 bg-surface-container flex items-center justify-center rounded border border-outline-variant group-hover:bg-primary group-hover:text-on-primary transition-colors">
                <span className="material-symbols-outlined">{s.icon}</span>
              </div>
              <span className="font-headline text-lg text-primary bg-surface px-2 py-1 border border-outline-variant rounded-sm group-hover:border-primary transition-colors">{s.cat}</span>
            </div>
            <h3 className="font-headline text-[24px] text-primary leading-tight uppercase mb-1">{s.title}</h3>
            <p className="font-label text-secondary uppercase text-xs mb-4">{s.host}</p>
            <div className="mt-auto pt-6 border-t border-outline-variant flex justify-between items-end">
              <div><span className="font-label text-xs uppercase text-secondary block">{s.prizeLabel}</span><span className="font-headline text-primary text-xl uppercase">{s.prize}</span></div>
              <div className="text-right"><span className="font-label text-xs uppercase text-secondary block">Closes</span><span className="font-body text-primary font-bold">{s.closes}</span></div>
            </div>
          </article>
        ))}
      </div>
      <div className="h-24" />
    </div>
  );
}
