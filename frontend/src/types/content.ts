/** Social stream post */
export interface Post {
  id: string;
  author: {
    name: string;
    handle: string;
    avatar?: string;
    initials?: string;
  };
  content: string;
  codeBlock?: string;
  image?: string;
  imageAlt?: string;
  timestamp: string;
  comments: number;
  reposts: number;
  likes: number;
}

/** Opportunity listing */
export interface Opportunity {
  id: string;
  title: string;
  type: string;
  matchScore: number;
  description: string;
  deadline?: string;
  actionLabel: string;
  actionIcon?: string;
  variant?: 'default' | 'featured' | 'dark';
}

/** Research paper */
export interface ResearchPaper {
  id: string;
  title: string;
  abstract: string;
  source: string;
  sourceId?: string;
  tags: string[];
  relevanceScore?: number;
  author?: string;
  views?: string;
  category?: string;
  imageUrl?: string;
}

/** Citation velocity entry */
export interface CitationEntry {
  rank: number;
  title: string;
  source: string;
  citationsPerWeek: number;
  barWidth: string;
}

/** GitHub repository */
export interface Repository {
  id: string;
  name: string;
  description: string;
  stars: string;
  language: string;
  tags?: string[];
  author?: {
    name: string;
    avatar?: string;
  };
  variant?: 'default' | 'featured';
}

/** Hackathon event */
export interface Hackathon {
  id: string;
  title: string;
  host: string;
  description?: string;
  prize: string;
  deadline: string;
  format?: string;
  teamSize?: string;
  category?: string;
  categoryIcon?: string;
  imageUrl?: string;
  variant?: 'featured' | 'elite' | 'standard';
}

/** Notification item */
export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  time: string;
  icon: string;
  iconColor?: string;
  isRead: boolean;
  actions?: { label: string; variant: 'primary' | 'secondary' }[];
  link?: { label: string; href: string };
}

/** Saved item */
export interface SavedItem {
  id: string;
  title: string;
  description: string;
  type: string;
  typeIcon: string;
  date?: string;
  readTime?: string;
  imageUrl?: string;
  variant?: 'featured' | 'standard' | 'data' | 'log' | 'quote';
}

/** Trending model */
export interface TrendingModel {
  rank: string;
  name: string;
  downloads: string;
}

/** Deadline item */
export interface DeadlineItem {
  day: string;
  month: string;
  title: string;
  subtitle: string;
}

/** Profile stat */
export interface ProfileStat {
  label: string;
  value: string;
  detail: string;
  icon: string;
}
