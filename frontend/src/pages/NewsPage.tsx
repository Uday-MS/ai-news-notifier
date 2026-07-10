import { useDocumentTitle } from '@/hooks/useDocumentTitle';

export default function NewsPage() {
  useDocumentTitle('AI News — Platinum Mist');

  return (
    <div className="p-8 max-w-[1600px] mx-auto w-full">
      {/* Newspaper Header */}
      <div className="text-center mb-10 py-6 border-y-4 border-primary">
        <h2 className="font-headline text-[5rem] leading-none uppercase tracking-tighter text-primary">Intelligence Feed</h2>
        <div className="flex justify-between items-center mt-4 px-4 font-label text-label-md text-on-surface-variant uppercase tracking-widest border-t border-outline-variant pt-2">
          <span>Vol. LXIV, No. 12</span>
          <span>Global Operations</span>
          <span>Updated: Just Now</span>
        </div>
      </div>

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Center Content */}
        <div className="lg:col-span-8 flex flex-col gap-8">
          {/* Hero Article */}
          <article className="flex flex-col xl:flex-row border border-primary bg-surface">
            <div className="p-8 xl:w-1/2 flex flex-col justify-center">
              <span className="font-label text-label-md uppercase tracking-widest text-secondary mb-4 block">Core Infrastructure</span>
              <h3 className="font-headline text-headline-lg text-primary mb-6">The Next Iteration of Autonomous Reasoning Clusters</h3>
              <p className="font-body text-body-lg text-on-surface-variant mb-6 leading-relaxed">
                Recent deployments indicate a shift from reactive prompting to persistent, background reasoning models. This architectural pivot fundamentally alters the compute cost structure and demands new paradigms for oversight and containment protocols.
              </p>
              <div className="flex items-center gap-3 mt-auto pt-6 border-t border-outline-variant">
                <img alt="Author" className="w-10 h-10 rounded-full border border-primary grayscale" src="https://lh3.googleusercontent.com/aida-public/AB6AXuB7pqlKqioyh5zBKi8GSRjg8wjiIhz_9Wo53FAW2Ae3loLrEaN649QEC7kPWsfZ3wiV1MLQONOZv4jrnqeIsMorgmgKeC3tF_8xnAVQb85N8DHbGi-S0swIYuj7LAOhNG5K0sVcg1Ipw4LHEdUg8rlsTP2ZkC5fAKhC5-rEnXjCSokjcdUtKAcPYI9y-V5fZ7UmHGURwjU0G6JDPrwt773SvEKTVLIZ-7326ncCvnfc0BzdXQW3fbpVKDeDwBbyfrojz5azCypCu6c" />
                <div>
                  <p className="font-label text-label-md text-primary font-bold uppercase">By Dr. Aris Thorne</p>
                  <p className="font-label text-sm text-outline">Lead Systems Architect</p>
                </div>
              </div>
            </div>
            <div className="xl:w-1/2 bg-primary-container p-1 border-l border-primary">
              <img alt="Server Infrastructure" className="w-full h-full object-cover min-h-[400px]" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBtrBRuBI1lzCmBJmTyeYJ1cC_LTxN2dT4Or8K8GK69on6uu6-LSW5M8BY569jndFnUofcIG9rRb9JnQnrcEezazjL_y3fyP08Mhzhwl0q-8l5hODDC3PqTIZVGkkVAkR_5hfjfQt4qExZWFW609zmkI9hD4xDGwTtSRy_dA5vMgXkRC5ds0bMFnk-oLDzprN7XCmZc4pLAN-rDYE0jwb7bMRUphQpXIOzY8th7tkR3tnTX_0KXE4L1aXn2b_gBi45CDTiXzALQGK8" />
            </div>
          </article>

          <div className="border-t-4 border-primary my-4" />

          {/* Secondary Articles */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <article className="group cursor-pointer">
              <img alt="Robotics" className="w-full h-64 object-cover border border-primary mb-4 grayscale group-hover:opacity-90 transition-opacity" src="https://lh3.googleusercontent.com/aida-public/AB6AXuA6gZK1VGTttT6FhMChddGAfXpgzOn821GtGjzp3KjmtZ1sMPN5MrYX3CJqI1AbITcO7WB28hgrsjLSNywbUNV1AD_IevBI3bWNdyh2SdDr8kEB8KV4jvn2DJ1OeHvpqaGWn4CVdC9ggODXOdc2ilXHrW2Dzt4xXQrg-YnkjBSLA9HJsafvVNiPh8MUXnp_FMr-6FDGS46cQ0T8ox7QOLzLZMgFnbVIYKggAu5SrvpUG2qciqJ58qLOqwigR2wzp7-acgndNJEl6Q4" />
              <span className="font-label text-label-md uppercase tracking-widest text-secondary mb-2 block">Kinetics &amp; Robotics</span>
              <h4 className="font-headline text-headline-md text-primary mb-3 group-hover:underline decoration-2 underline-offset-4">Bipedal Logistics Reach Parity</h4>
              <p className="font-body text-body-md text-on-surface-variant">Supply chain implementations show a 40% reduction in fulfillment latency when utilizing the new Series-7 units in constrained environments.</p>
            </article>
            <article className="group cursor-pointer">
              <div className="w-full h-64 border border-primary mb-4 bg-surface-container flex flex-col justify-center items-center p-6 text-center">
                <span className="material-symbols-outlined text-[48px] text-primary mb-4">gavel</span>
                <h4 className="font-headline text-headline-md text-primary leading-tight">EU AI Act: Compliance Horizon Narrows</h4>
              </div>
              <span className="font-label text-label-md uppercase tracking-widest text-secondary mb-2 block">Regulation</span>
              <p className="font-body text-body-md text-on-surface-variant">Immediate action required for all generative models processing data within the union. Penalties set to scale with parameter counts.</p>
            </article>
          </div>
        </div>

        {/* Right Sidebar */}
        <aside className="lg:col-span-4 flex flex-col gap-8">
          {/* CTA */}
          <div className="bg-primary p-8 border border-primary">
            <span className="material-symbols-outlined text-on-primary text-4xl mb-4 icon-fill block">summarize</span>
            <h3 className="font-headline text-headline-md text-on-primary mb-2">Executive Briefing</h3>
            <p className="font-body text-body-md text-outline-variant mb-6">Compile a cross-referenced synthesis of the last 24 hours of intelligence updates into a secure, readable format.</p>
            <button className="w-full bg-surface text-primary font-headline text-headline-sm py-4 uppercase tracking-widest hover:bg-surface-dim transition-colors border border-transparent hover:border-primary cursor-pointer">Generate Briefing</button>
          </div>

          {/* Trending Models */}
          <div className="border border-primary bg-surface p-6">
            <div className="flex items-center gap-2 mb-6 border-b border-primary pb-4">
              <span className="material-symbols-outlined text-primary">monitoring</span>
              <h3 className="font-headline text-2xl uppercase tracking-wider text-primary">Trending Models</h3>
            </div>
            <div className="flex flex-col gap-4">
              {[
                { name: 'Nexus-V4 (Instruct)', info: '70B Parameters • Open Weights', trend: 'trending_up' },
                { name: 'Apollo Vision-Pro', info: 'Multimodal • Proprietary', trend: 'trending_up' },
                { name: 'Whisper-X Turbo', info: 'Audio ASR • Quantized', trend: 'trending_flat' },
              ].map((m) => (
                <div key={m.name} className="flex justify-between items-center p-3 hover:bg-surface-container-high transition-colors cursor-pointer border border-transparent hover:border-outline-variant">
                  <div>
                    <p className="font-headline text-lg text-primary">{m.name}</p>
                    <p className="font-label text-sm text-secondary">{m.info}</p>
                  </div>
                  <span className="material-symbols-outlined text-secondary">{m.trend}</span>
                </div>
              ))}
            </div>
            <button className="w-full mt-6 py-2 border-t border-outline-variant font-label text-label-md uppercase tracking-widest text-primary hover:text-secondary transition-colors text-center bg-transparent border-l-0 border-r-0 border-b-0 cursor-pointer">View Model Registry</button>
          </div>

          {/* System Status */}
          <div className="border border-primary bg-surface p-6">
            <h3 className="font-label text-label-md uppercase tracking-widest text-secondary mb-4 border-b border-outline-variant pb-2">System Status</h3>
            <div className="grid grid-cols-2 gap-4">
              <div><p className="font-headline text-3xl text-primary">99.9%</p><p className="font-label text-xs text-on-surface-variant uppercase">Uptime</p></div>
              <div><p className="font-headline text-3xl text-primary">12ms</p><p className="font-label text-xs text-on-surface-variant uppercase">Avg Latency</p></div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
