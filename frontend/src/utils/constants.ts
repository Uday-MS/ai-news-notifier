import type { NavItem } from '@/types/navigation';

/** Sidebar navigation items */
export const NAV_ITEMS: NavItem[] = [
  { to: '/', icon: 'home', label: 'Home' },
  { to: '/news', icon: 'newspaper', label: 'AI News' },
  { to: '/opportunities', icon: 'lightbulb', label: 'Opportunities' },
  { to: '/research', icon: 'biotech', label: 'Research' },
  { to: '/github', icon: 'terminal', label: 'GitHub' },
  { to: '/hackathons', icon: 'emoji_events', label: 'Hackathons' },
  { to: '/saved', icon: 'bookmark', label: 'Saved' },
  { to: '/notifications', icon: 'notifications', label: 'Notifications' },
  { to: '/profile', icon: 'account_circle', label: 'Profile' },
  { to: '/settings', icon: 'settings', label: 'Settings' },
];
