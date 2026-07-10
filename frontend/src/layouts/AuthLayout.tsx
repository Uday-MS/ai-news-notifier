import { Outlet } from 'react-router-dom';

/**
 * Full-screen layout for authentication pages.
 * Centered content with subtle themed background.
 */
export function AuthLayout() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-on-surface p-4">
      <Outlet />
    </div>
  );
}
