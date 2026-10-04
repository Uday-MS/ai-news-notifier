/**
 * AppLayout — Intelligence platform shell.
 * Left nav rail + fluid center feed + optional inspector sidebar.
 */

import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { SideNav } from '@/components/navigation/SideNav';
import { RightSidebar } from '@/components/widgets/RightSidebar';
import { getUnread } from '@/services/notificationService';

const FULL_WIDTH_ROUTES = ['/settings', '/profile'];

export function AppLayout() {
  const location = useLocation();
  const [unreadCount, setUnreadCount] = useState(0);
  const hideRightSidebar = FULL_WIDTH_ROUTES.some((r) => location.pathname === r || location.pathname.startsWith(r + '/'));

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
    <div className="min-h-screen bg-background text-on-background">
      <SideNav />

      {/* Main content area — offset by nav rail width */}
      <div className={`lg:ml-[64px] xl:ml-[240px] flex justify-center`}>
        <div className={`flex w-full ${hideRightSidebar ? 'max-w-[720px]' : 'max-w-[1100px]'}`}>
          {/* Center feed column */}
          <main
            className="flex-1 min-h-screen w-full max-w-[680px] border-x border-outline-variant"
            role="main"
            aria-label="Main content"
          >
            <div className="page-transition">
              <Outlet />
            </div>
          </main>

          {/* Intelligence sidebar */}
          {!hideRightSidebar && <RightSidebar />}
        </div>
      </div>

      {/* Mobile bottom nav */}
      <nav
        className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-surface/95 backdrop-blur-md border-t border-outline-variant flex justify-around items-center h-14"
        role="navigation"
        aria-label="Mobile navigation"
      >
        {[
          { to: '/', icon: 'home', end: true },
          { to: '/news', icon: 'search' },
          { to: '/notifications', icon: 'notifications', badge: unreadCount },
          { to: '/saved', icon: 'bookmark' },
          { to: '/profile', icon: 'person' },
        ].map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.end}
            className={({ isActive }) =>
              `flex flex-col items-center text-[10px] gap-0.5 no-underline p-2 transition-colors ${
                isActive ? 'text-primary' : 'text-on-surface-variant'
              }`
            }
          >
            <span className="material-symbols-outlined text-xl relative">
              {n.icon}
              {n.badge && n.badge > 0 ? (
                <span className="absolute -top-1 -right-1.5 min-w-[14px] h-[14px] flex items-center justify-center bg-[var(--c-danger)] text-white text-[8px] font-bold rounded-full px-0.5 leading-none">
                  {n.badge > 99 ? '99+' : n.badge}
                </span>
              ) : null}
            </span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
