import { Outlet } from 'react-router-dom';

/**
 * AuthLayout — Full-screen intelligence auth shell.
 * Dark obsidian background with centered content.
 */
export function AuthLayout() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-on-surface p-4">
      <Outlet />
    </div>
  );
}
