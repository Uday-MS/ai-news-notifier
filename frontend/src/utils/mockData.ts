import type { Post, TrendingModel, DeadlineItem } from '@/types/content';
import type { Organization } from '@/components/widgets/SuggestedOrganizations';

/* ── Home Page Data ──────────────────────────────────────────────────────── */

export const POSTS: Post[] = [
  {
    id: '1',
    author: {
      name: 'Dr. E. Thorne',
      handle: '@ethorne_ai',
      avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAsUe3YPcNPbve56eTEFgSVBghSTaiskckvjr4ThSXPJ-xdJNbEGUgcKL7j7d2belWoAtUaoEV5jEn5xmqMRn5hSzh7tuGCJHEhjyr14C1SXkiYQWaak5E__NPpNt-i15pKFz3jmlp_M-aNdWM7TA6gtPMs9rn_yyb2x1hy5y_sqcR86594zaRqtKsuNvtDIp6DpyoZ9NURZbC8dB3n1AyRHTK2SVaTV4Xqp8DwwpSCR3_8OGmvti0EQvzasNYfdtzVui_hx51qQtM',
    },
    content: 'Observed significant latency improvements in the new LLM inference engine when leveraging sparse attention mechanisms. The trade-off in perplexity is minimal compared to the throughput gains. Full report dropping in Research tab tomorrow.',
    codeBlock: '> INF_ENGINE_V4_INIT\n> STATUS: STABLE\n> THROUGHPUT: +34% (YOY)',
    timestamp: '2h',
    comments: 12,
    reposts: 4,
    likes: 156,
  },
  {
    id: '2',
    author: {
      name: 'Nexus Systems',
      handle: '@nexus_sys',
      initials: 'NS',
    },
    content: 'Hardware deployment phase 3 complete. Expanding the cluster grid across sector 7. The structural integrity of the new cooling arrays is performing beyond initial simulations.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC09pNecxRdRTbwiKKordm4LeEfSQ0oupI2pp2WZWXZrQz8vc1XeVUChN-Tu0O0ifssgQn6vSH77Xxuz8oEcWY0oVLEDtQpa_aF5ANCSwXeaKjiCXtrN7xnEBGirnBcpe8Zn-wD-qtaWO3bIF_471DUecWU45HEToH-JcYxe72SSfHwQxeX1tP81EhqkTWsdGM0gmJtSE6_qmzgPBiD0bOhgEMA0UNTik7bPTmW7rp0cysHoMqdlwGvEQyxJvfApefrIB4hHzu1BNk',
    imageAlt: 'Server farm interior',
    timestamp: '5h',
    comments: 89,
    reposts: 12,
    likes: 402,
  },
  {
    id: '3',
    author: {
      name: 'V. Croft',
      handle: '@croft_dev',
      avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBz4S_TFawMHwKP7Ll04pdoDPpO6NlLfi_4ux2jkJGWvi76CnEZEd8MOaFAXnd9Wx9HzwjD5nYv8-klAjs_-hO4zE-Qi7tmdIHV34wZc8mUGQ4rbARBUix7kh12plsdnFrqC8-pfm41GGRhd2wLNpo5MyRFg85Y9tVibKkQU503ilBnsFHNbQFsWipjKMJHriiZicaA958nUrPagCRn2ZhcYj-POM_udLa-7ciMNCuKyt-YjF7XmwMpLCc3PDdVPdhFpj-ysWxzMlo',
    },
    content: 'Just pushed a structural refactor to the core pipeline repository. Eliminated 4 redundant data transformation steps. The architecture is much cleaner now. Code review requested.',
    timestamp: '8h',
    comments: 3,
    reposts: 1,
    likes: 45,
  },
];

export const TRENDING_MODELS: TrendingModel[] = [
  { rank: 'Rank 01', name: 'Titan-V2-Base', downloads: '12.4M Downloads' },
  { rank: 'Rank 02', name: 'Echo-Instruct-7B', downloads: '8.1M Downloads' },
  { rank: 'Rank 03', name: 'Vision-Core-X', downloads: '5.9M Downloads' },
];

export const DEADLINES: DeadlineItem[] = [
  { day: '12', month: 'Oct', title: 'Hackathon Submission', subtitle: 'Global AI Challenge' },
  { day: '18', month: 'Oct', title: 'Grant Application', subtitle: 'Research Foundation' },
];

export const RECOMMENDED_TOPICS = [
  '#NeuralNetworks',
  '#ComputeScaling',
  '#EthicsAI',
  '#HardwareOpt',
  '#Transformers',
];

export const SUGGESTED_ORGANIZATIONS: Organization[] = [
  {
    id: 'org-1',
    name: 'DeepMind',
    handle: '@deepmind',
    description: 'AI research lab',
  },
  {
    id: 'org-2',
    name: 'Hugging Face',
    handle: '@huggingface',
    description: 'Open-source AI community',
  },
  {
    id: 'org-3',
    name: 'Anthropic',
    handle: '@anthropic',
    description: 'AI safety research',
  },
];
