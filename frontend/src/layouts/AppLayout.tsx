import { useState, useEffect } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { SideNav } from '@/components/navigation/SideNav';
import { RightSidebar } from '@/components/widgets/RightSidebar';
import { getUnread } from '@/services/notificationService';

/**
 * Three-column application layout inspired by X (Twitter).
 * Left: SideNav (fixed) | Center: Outlet (scrollable, max-width) | Right: Widgets (sticky)
 */
export function AppLayout() {
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    async function fetchUnread() {
      try {
        const result = await getUnread(1, 0);
        if (result.success && result.data) {
          setUnreadCount(result.data.pagination.total);
        }
      } catch { /* silent */ }
    }
    fetchUnread();
    timer = setInterval(fetchUnread, 60000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex justify-center min-h-screen bg-background text-on-background font-body">
      {/* Left Sidebar */}
      <SideNav />

      {/* Center + Right container */}
      <div className="flex w-full xl:max-w-[1100px] lg:max-w-[650px] lg:ml-[72px] xl:ml-[275px]">
        {/* Center Feed — wider for better content readability */}
        <main
          className="flex-1 min-h-screen border-x border-outline w-full max-w-[700px]"
          role="main"
          aria-label="Main content"
        >
          <div className="page-transition">
            <Outlet />
          </div>
        </main>

        {/* Right Sidebar */}
        <RightSidebar />
      </div>

      {/* Mobile bottom nav */}
      <nav
        className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-surface/95 backdrop-blur-md border-t border-outline flex justify-around items-center h-14"
        role="navigation"
        aria-label="Mobile navigation"
      >
        <NavLink to="/" end className={({ isActive }) => `flex flex-col items-center text-xs gap-0.5 no-underline p-2 ${isActive ? 'text-primary' : 'text-on-surface-variant'}`}>
          <span className={`material-symbols-outlined text-xl`}>home</span>
        </NavLink>
        <NavLink to="/news" className={({ isActive }) => `flex flex-col items-center text-xs gap-0.5 no-underline p-2 ${isActive ? 'text-primary' : 'text-on-surface-variant'}`}>
          <span className="material-symbols-outlined text-xl">search</span>
        </NavLink>
        <NavLink to="/notifications" className={({ isActive }) => `flex flex-col items-center text-xs gap-0.5 no-underline relative p-2 ${isActive ? 'text-primary' : 'text-on-surface-variant'}`}>
          <span className="material-symbols-outlined text-xl relative">
            notifications
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1.5 min-w-[16px] h-[16px] flex items-center justify-center bg-primary text-on-primary text-[9px] font-bold rounded-full px-0.5 leading-none">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </span>
        </NavLink>
        <NavLink to="/saved" className={({ isActive }) => `flex flex-col items-center text-xs gap-0.5 no-underline p-2 ${isActive ? 'text-primary' : 'text-on-surface-variant'}`}>
          <span className="material-symbols-outlined text-xl">bookmark</span>
        </NavLink>
        <NavLink to="/profile" className={({ isActive }) => `flex flex-col items-center text-xs gap-0.5 no-underline p-2 ${isActive ? 'text-primary' : 'text-on-surface-variant'}`}>
          <span className="material-symbols-outlined text-xl">person</span>
        </NavLink>
      </nav>
    </div>
  );
}
