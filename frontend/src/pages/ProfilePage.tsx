import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useAuth } from '@/store/AuthContext';

export default function ProfilePage() {
  useDocumentTitle('Profile — AI News Notifier');
  const { user } = useAuth();

  const stats = [
    { label: 'Papers Read', value: '342', detail: '+12 this week', icon: 'menu_book' },
    { label: 'Models Trained', value: '87', detail: '99.4% avg success rate', icon: 'model_training' },
    { label: 'Apps Deployed', value: '14', detail: 'Zero downtime', icon: 'dns' },
    { label: 'Global Rank', value: 'Top 2%', detail: 'In architectural design', icon: 'emoji_events' },
  ];

  const operations = [
    { icon: 'commit', bgClass: 'bg-primary text-on-primary', title: 'Optimized Transformer Topology', time: '2 hours ago', desc: 'Reduced inference latency by 14% through structural pruning and quantization strategies in the core neural engine.' },
    { icon: 'description', bgClass: 'bg-surface-container text-primary border border-outline', title: 'Published: Brutalist AI Architectures', time: 'Yesterday', desc: 'Internal research paper detailing a methodology for removing unnecessary complexity in model scaling.' },
    { icon: 'terminal', bgClass: 'bg-surface-container text-primary border border-outline', title: 'System Override: Node Alpha-7', time: 'Oct 12, 2023', desc: 'Emergency manual recalibration of distributed training cluster to prevent thermal throttling.' },
  ];

  return (
    <div className="p-4 md:p-[64px] overflow-y-auto">
      <div className="max-w-7xl mx-auto flex flex-col gap-6">
        {/* Header */}
        <header className="flex justify-between items-end border-b-2 border-primary pb-4 mb-2">
          <div>
            <h2 className="font-label text-secondary uppercase tracking-widest mb-1 text-sm">Intelligence Profile</h2>
            <h1 className="font-headline text-headline-lg text-primary uppercase">{user?.full_name || 'Agent'}</h1>
          </div>
          <div className="hidden md:flex gap-3">
            <button className="border-2 border-primary text-primary font-headline px-6 py-2 uppercase hover:bg-surface-container transition-colors bg-transparent cursor-pointer">Edit Profile</button>
            <button className="bg-primary text-on-primary font-headline px-6 py-2 uppercase hover:bg-primary-container transition-colors border-none cursor-pointer">Share Intel</button>
          </div>
        </header>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Hero */}
          <div className="col-span-1 md:col-span-8 bg-surface-container-lowest border-2 border-primary p-8 relative overflow-hidden flex flex-col justify-end min-h-[320px]">
            <div className="absolute inset-0 opacity-10 pointer-events-none" style={{ backgroundImage: 'repeating-linear-gradient(45deg, #16191e 0, #16191e 1px, transparent 1px, transparent 10px)' }} />
            <div className="relative z-10 flex flex-col md:flex-row items-end gap-6">
              <div className="w-32 h-32 md:w-40 md:h-40 bg-surface-container border-2 border-primary overflow-hidden shrink-0">
                <img alt="Profile" className="w-full h-full object-cover grayscale" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDSlnc__5LQF8B_qprmq4YsMQ6UsMvuUhM02redY3yDHOXHT9wfUSTrV0J_mXsDuISkPX9O0PSgv4WEjLAnDXr__OMo2gMxCN0xTHDuxvccP1PzjpSbPzXXB0OPkw0DkMOr-Ww7fsbZ_ODydkKHooYkfImBThXgyt2Sk1_m2ydUxPuO1K7Ny0B6RFLJUltgfA0ofRfqQfbyJUXcn_H6quzYECQydF4FHNJ82LWZf0Sak_OyOLCj9Vx4qNTPvDnPYkvkWh--0xN8YMI" />
              </div>
              <div className="flex-1 pb-2">
                <h3 className="font-headline text-headline-md text-primary leading-none uppercase mb-2">Senior AI Research Engineer</h3>
                <p className="font-body text-body-lg text-on-surface-variant max-w-xl">Specializing in generative architectures, neural structural integrity, and brutalist optimization algorithms. Deployed 14 enterprise-scale models globally.</p>
                <div className="flex gap-4 mt-6">
                  <div className="flex items-center gap-2 text-sm font-label uppercase text-secondary"><span className="material-symbols-outlined text-lg">location_on</span> Neo-Tokyo / Remote</div>
                  <div className="flex items-center gap-2 text-sm font-label uppercase text-secondary"><span className="material-symbols-outlined text-lg">business</span> Cybernetics Division</div>
                </div>
              </div>
            </div>
          </div>

          {/* Security Card */}
          <div className="col-span-1 md:col-span-4 bg-primary text-on-primary border-2 border-primary p-8 flex flex-col justify-between">
            <div className="font-label uppercase tracking-widest text-inverse-primary text-sm border-b border-surface-tint pb-2 mb-4">Security Clearance</div>
            <div><div className="font-headline text-6xl leading-none mb-2">Lvl 08</div><p className="font-body text-body-md text-inverse-primary">Authorized for critical system overrides and experimental core access.</p></div>
            <div className="mt-8 pt-4 border-t border-surface-tint flex justify-between items-center">
              <span className="font-label text-xs uppercase text-inverse-primary">Status</span>
              <span className="flex items-center gap-2 font-headline text-sm tracking-wider"><div className="w-2 h-2 rounded-full bg-surface-container-lowest animate-pulse" /> ACTIVE / ONLINE</span>
            </div>
          </div>

          {/* Stats */}
          {stats.map((s) => (
            <div key={s.label} className="col-span-1 md:col-span-3 bg-surface-container-lowest border border-outline p-6 hover:border-primary transition-colors group cursor-default">
              <div className="font-label text-secondary uppercase text-xs mb-4 flex justify-between items-center">{s.label}<span className="material-symbols-outlined text-lg text-outline-variant group-hover:text-primary transition-colors">{s.icon}</span></div>
              <div className="font-headline text-headline-md text-primary">{s.value}</div>
              <div className="font-body text-sm text-on-surface-variant mt-2">{s.detail}</div>
            </div>
          ))}

          {/* Core Stack */}
          <div className="col-span-1 md:col-span-4 bg-surface-container-lowest border-2 border-outline-variant p-6 flex flex-col">
            <h3 className="font-headline text-xl uppercase text-primary border-b-2 border-primary pb-2 mb-6">Core Stack</h3>
            <div className="flex-1 space-y-4">
              {[{ label: 'Frameworks', items: ['PyTorch', 'TensorFlow', 'JAX'] }, { label: 'Languages', items: ['Python', 'Rust', 'C++'] }, { label: 'Infrastructure', items: ['Kubernetes', 'Docker', 'AWS Sagemaker'] }].map((g) => (
                <div key={g.label}><div className="font-label text-xs uppercase text-secondary mb-2">{g.label}</div><div className="flex flex-wrap gap-2">{g.items.map((i) => <span key={i} className="bg-surface-container px-3 py-1 text-sm font-body text-on-surface border border-outline-variant">{i}</span>)}</div></div>
              ))}
            </div>
          </div>

          {/* Recent Operations */}
          <div className="col-span-1 md:col-span-8 bg-surface-container-lowest border-2 border-outline-variant p-6">
            <div className="flex justify-between items-end border-b-2 border-primary pb-2 mb-6">
              <h3 className="font-headline text-xl uppercase text-primary">Recent Operations</h3>
              <a className="font-label text-sm uppercase text-secondary hover:text-primary transition-colors flex items-center gap-1" href="#">View Log <span className="material-symbols-outlined text-sm">arrow_forward</span></a>
            </div>
            <div className="flex flex-col gap-4">
              {operations.map((op) => (
                <div key={op.title} className="group flex gap-4 p-4 border border-transparent hover:border-outline-variant hover:bg-surface-container-low transition-all">
                  <div className={`w-12 h-12 flex items-center justify-center shrink-0 ${op.bgClass}`}><span className="material-symbols-outlined">{op.icon}</span></div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start mb-1"><h4 className="font-headline text-lg uppercase text-primary">{op.title}</h4><span className="font-label text-xs text-secondary">{op.time}</span></div>
                    <p className="font-body text-on-surface-variant text-sm">{op.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
