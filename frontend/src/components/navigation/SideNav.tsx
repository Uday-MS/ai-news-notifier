/**
 * SideNav — Intelligence platform command rail.
 * 64px collapsed (lg) → 240px expanded (xl).
 * Sharp 4px radius, instrument-grade design.
 */

import { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { NAV_ITEMS } from '@/utils/constants';
import { useAuth } from '@/store/AuthContext';
import { cn } from '@/utils/cn';
import { getUnread } from '@/services/notificationService';

export function SideNav() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    async function fetchUnread() {
      try {
        const result = await getUnread(1, 0);
        if (result.success && result.data) setUnreadCount(result.data.pagination.total);
      } catch { /* silent */ }
    }
    fetchUnread();
    timer = setInterval(fetchUnread, 60000);
    return () => clearInterval(timer);
  }, []);

  return (
    <nav
      className="hidden lg:flex flex-col fixed left-0 top-0 h-screen z-40 border-r border-outline-variant xl:w-[240px] lg:w-[64px] bg-surface"
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Brand */}
      <div className="p-3 xl:px-4">
        <NavLink to="/" className="flex items-center gap-2.5 px-2 py-2 no-underline group">
          <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-primary text-lg icon-fill">hub</span>
          </div>
          <span className="hidden xl:block font-headline text-[15px] font-semibold text-on-surface tracking-tight">
            Nexus<span className="text-primary">AI</span>
          </span>
        </NavLink>
      </div>

      {/* Nav Items */}
      <div className="flex-1 overflow-y-auto no-scrollbar flex flex-col gap-0.5 px-2 mt-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn('nav-item relative', isActive && 'active')
            }
          >
            <span className="material-symbols-outlined text-[22px] relative shrink-0">
              {item.icon}
              {item.to === '/notifications' && unreadCount > 0 && (
                <span className="absolute -top-1 -right-1.5 min-w-[16px] h-[16px] flex items-center justify-center bg-[var(--c-danger)] text-white text-[9px] font-bold rounded-full px-0.5 leading-none font-mono">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </span>
            <span className="hidden xl:inline text-[14px] leading-none truncate">{item.label}</span>
          </NavLink>
        ))}
      </div>

      {/* User */}
      {user && (
        <div className="p-2 xl:px-3 border-t border-outline-variant">
          <button
            onClick={logout}
            className="w-full flex items-center gap-2.5 nav-item bg-transparent border-none cursor-pointer text-left"
            title="Logout"
          >
            <div className="w-8 h-8 rounded bg-[var(--c-overlay)] text-on-surface flex items-center justify-center font-semibold text-xs shrink-0 font-headline">
              {user.full_name?.charAt(0)?.toUpperCase() || user.email.charAt(0).toUpperCase()}
            </div>
            <div className="hidden xl:flex flex-col min-w-0 flex-1">
              <span className="font-medium text-[13px] text-on-surface truncate">{user.full_name || 'User'}</span>
              <span className="text-[11px] text-on-surface-variant truncate font-mono">{user.email}</span>
            </div>
            <span className="material-symbols-outlined text-on-surface-variant hidden xl:inline text-base">logout</span>
          </button>
        </div>
      )}
    </nav>
  );
}
