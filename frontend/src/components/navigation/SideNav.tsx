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
    <nav className="hidden lg:flex flex-col fixed left-0 top-0 h-screen z-40 border-r border-outline xl:w-[275px] lg:w-[72px] bg-surface" role="navigation" aria-label="Main navigation">
      <div className="p-3 xl:px-3">
        <NavLink to="/" className="nav-pill inline-flex !p-3 !gap-0">
          <span className="material-symbols-outlined text-primary text-[28px] icon-fill">hub</span>
        </NavLink>
      </div>

      <div className="flex-1 overflow-y-auto no-scrollbar flex flex-col gap-0.5 px-2">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.to === '/'} className={({ isActive }) => cn('nav-pill relative', isActive && 'active')}>
            <span className="material-symbols-outlined text-[26px] relative">
              {item.icon}
              {item.to === '/notifications' && unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-primary text-on-primary text-[10px] font-bold rounded-full px-1 leading-none">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </span>
            <span className="text-xl hidden xl:inline leading-none">{item.label}</span>
          </NavLink>
        ))}
      </div>

      <div className="p-3 xl:px-4">
        <button onClick={() => navigate('/news')}
          className="w-full bg-primary text-on-primary rounded-full py-3 px-4 font-bold text-[17px] hover:bg-[var(--c-accent-hover)] active:scale-[0.97] transition-all border-none cursor-pointer">
          <span className="hidden xl:inline">Explore</span>
          <span className="xl:hidden material-symbols-outlined text-xl">search</span>
        </button>
      </div>

      {user && (
        <div className="p-3 xl:px-3 mb-2">
          <button onClick={logout} className="w-full flex items-center gap-3 nav-pill hover:bg-[var(--c-elevated)] bg-transparent border-none cursor-pointer text-left" title="Logout">
            <div className="w-10 h-10 rounded-full bg-[var(--c-elevated)] text-on-surface flex items-center justify-center font-semibold text-sm shrink-0">
              {user.full_name?.charAt(0)?.toUpperCase() || user.email.charAt(0).toUpperCase()}
            </div>
            <div className="hidden xl:flex flex-col min-w-0 flex-1">
              <span className="font-semibold text-[15px] text-on-surface truncate">{user.full_name || 'User'}</span>
              <span className="text-[13px] text-on-surface-variant truncate">{user.email}</span>
            </div>
            <span className="material-symbols-outlined text-on-surface-variant hidden xl:inline text-lg">more_horiz</span>
          </button>
        </div>
      )}
    </nav>
  );
}
