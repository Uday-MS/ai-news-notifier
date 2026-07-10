import { Outlet } from 'react-router-dom';
import { SideNav } from '@/components/navigation/SideNav';
import { RightSidebar } from '@/components/widgets/RightSidebar';

/**
 * Three-column application layout inspired by X (Twitter).
 * Left: SideNav (fixed) | Center: Outlet (scrollable, max-width) | Right: Widgets (sticky)
 */
export function AppLayout() {
  return (
    <div className="flex justify-center min-h-screen bg-background text-on-background font-body">
      {/* Left Sidebar */}
      <SideNav />

      {/* Center + Right container */}
      <div className="flex w-full xl:max-w-[1050px] lg:max-w-[650px] lg:ml-[72px] xl:ml-[275px]">
        {/* Center Feed */}
        <main className="flex-1 min-h-screen border-x border-outline max-w-[600px] w-full">
          <Outlet />
        </main>

        {/* Right Sidebar */}
        <RightSidebar />
      </div>

      {/* Mobile bottom nav */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-surface border-t border-outline flex justify-around items-center h-14">
        <a href="/" className="flex flex-col items-center text-on-surface-variant text-xs gap-0.5 no-underline">
          <span className="material-symbols-outlined text-xl">home</span>
        </a>
        <a href="/news" className="flex flex-col items-center text-on-surface-variant text-xs gap-0.5 no-underline">
          <span className="material-symbols-outlined text-xl">search</span>
        </a>
        <a href="/notifications" className="flex flex-col items-center text-on-surface-variant text-xs gap-0.5 no-underline">
          <span className="material-symbols-outlined text-xl">notifications</span>
        </a>
        <a href="/profile" className="flex flex-col items-center text-on-surface-variant text-xs gap-0.5 no-underline">
          <span className="material-symbols-outlined text-xl">person</span>
        </a>
      </nav>
    </div>
  );
}
