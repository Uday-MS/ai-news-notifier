import { NavLink } from 'react-router-dom';
import { NAV_ITEMS } from '@/utils/constants';
import { useAuth } from '@/store/AuthContext';
import { cn } from '@/utils/cn';

/**
 * X-inspired left sidebar navigation.
 * Full labels on xl+, icon-only on lg, hidden on smaller screens.
 */
export function SideNav() {
  const { user, logout } = useAuth();

  return (
    <nav className="hidden lg:flex flex-col fixed left-0 top-0 h-screen z-40 border-r border-outline xl:w-[275px] lg:w-[72px] bg-surface">
      {/* Logo */}
      <div className="p-4 xl:px-4">
        <NavLink to="/" className="nav-pill inline-flex !p-3 !gap-0">
          <span className="material-symbols-outlined text-primary text-[28px] icon-fill">hub</span>
        </NavLink>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto no-scrollbar flex flex-col gap-0.5 px-2">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'nav-pill',
                isActive && 'active'
              )
            }
          >
            <span className="material-symbols-outlined text-[26px]">
              {item.icon}
            </span>
            <span className="text-[1.2rem] font-body hidden xl:inline leading-none">
              {item.label}
            </span>
          </NavLink>
        ))}
      </div>

      {/* Post CTA */}
      <div className="p-3 xl:px-4">
        <button className="w-full bg-primary text-on-primary rounded-full py-3 px-4 font-bold text-body-md hover:opacity-90 transition-opacity border-none cursor-pointer shadow-lg">
          <span className="hidden xl:inline">Broadcast</span>
          <span className="xl:hidden material-symbols-outlined text-xl">edit_square</span>
        </button>
      </div>

      {/* User Info + Logout */}
      {user && (
        <div className="p-3 xl:px-4 mb-3">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 nav-pill hover:bg-surface-container xl:pr-3 bg-transparent border-none cursor-pointer text-left"
            title="Logout"
          >
            <div className="w-10 h-10 rounded-full bg-primary text-on-primary flex items-center justify-center font-bold text-sm shrink-0">
              {user.full_name?.charAt(0)?.toUpperCase() || user.email.charAt(0).toUpperCase()}
            </div>
            <div className="hidden xl:flex flex-col min-w-0 flex-1">
              <span className="font-body font-bold text-sm text-on-surface truncate">{user.full_name || 'User'}</span>
              <span className="font-body text-xs text-on-surface-variant truncate">{user.email}</span>
            </div>
            <span className="material-symbols-outlined text-on-surface-variant hidden xl:inline text-lg">more_horiz</span>
          </button>
        </div>
      )}
    </nav>
  );
}
