import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useTheme, type Theme } from '@/hooks/useTheme';
import { cn } from '@/utils/cn';

const THEME_OPTIONS: { value: Theme; label: string; icon: string }[] = [
  { value: 'light', label: 'Light', icon: 'light_mode' },
  { value: 'dark', label: 'Dark', icon: 'dark_mode' },
  { value: 'system', label: 'System', icon: 'contrast' },
];

export default function SettingsPage() {
  useDocumentTitle('Settings — AI News Notifier');
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex flex-col min-h-screen">
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 bg-surface/80 backdrop-blur-md border-b border-outline px-4 py-3">
        <h2 className="text-xl font-bold font-body text-on-surface">Settings</h2>
      </div>

      <div className="p-4 flex flex-col gap-6">
        {/* Theme Section */}
        <section className="bg-surface-container-low rounded-2xl p-5">
          <h3 className="font-body font-bold text-on-surface text-lg mb-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-xl">palette</span>
            Display
          </h3>
          <p className="text-on-surface-variant text-sm font-body mb-4">Manage your display preferences.</p>

          <div className="mb-4">
            <label className="font-body text-sm font-medium text-on-surface-variant block mb-3">Theme</label>
            <div className="grid grid-cols-3 gap-3">
              {THEME_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setTheme(opt.value)}
                  className={cn(
                    'flex flex-col items-center gap-2 py-4 px-3 rounded-xl border-2 transition-all cursor-pointer bg-surface font-body',
                    theme === opt.value
                      ? 'border-primary text-primary'
                      : 'border-outline text-on-surface-variant hover:border-on-surface-variant'
                  )}
                >
                  <span className={cn('material-symbols-outlined text-2xl', theme === opt.value && 'icon-fill')}>
                    {opt.icon}
                  </span>
                  <span className="text-sm font-medium">{opt.label}</span>
                  {theme === opt.value && (
                    <span className="w-2 h-2 rounded-full bg-primary" />
                  )}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="font-body text-sm font-medium text-on-surface-variant block mb-2">Data Density</label>
            <select className="input-field">
              <option>Comfortable (Standard)</option>
              <option>Compact (High Density)</option>
              <option>Spacious (Presentation)</option>
            </select>
          </div>
        </section>

        {/* Account Section */}
        <section className="bg-surface-container-low rounded-2xl p-5">
          <h3 className="font-body font-bold text-on-surface text-lg mb-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-xl">person</span>
            Account
          </h3>
          <p className="text-on-surface-variant text-sm font-body mb-4">Manage your account information.</p>

          <div className="flex flex-col gap-4">
            <div>
              <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Full Name</label>
              <input className="input-field" type="text" defaultValue="Dr. Aris Thorne" />
            </div>
            <div>
              <label className="font-body text-sm font-medium text-on-surface-variant block mb-1.5">Email</label>
              <input className="input-field" type="email" defaultValue="a.thorne@example.com" />
            </div>
          </div>
        </section>

        {/* Security Section */}
        <section className="bg-surface-container-low rounded-2xl p-5">
          <h3 className="font-body font-bold text-on-surface text-lg mb-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-xl">shield</span>
            Security
          </h3>
          <p className="text-on-surface-variant text-sm font-body mb-4">Manage passwords and access.</p>

          <div className="flex flex-col gap-3">
            <div className="flex justify-between items-center py-2">
              <div>
                <p className="font-body font-medium text-sm text-on-surface">Password</p>
                <p className="font-body text-sm text-on-surface-variant">Last changed 45 days ago</p>
              </div>
              <button className="px-4 py-2 rounded-full border border-outline text-on-surface font-body font-bold text-sm hover:bg-surface-container transition-colors bg-transparent cursor-pointer">
                Update
              </button>
            </div>
            <div className="flex justify-between items-center py-2 border-t border-outline">
              <div>
                <p className="font-body font-medium text-sm text-on-surface">Two-Factor Authentication</p>
                <p className="font-body text-sm text-on-surface-variant">Not enabled</p>
              </div>
              <button className="px-4 py-2 rounded-full bg-primary text-on-primary font-body font-bold text-sm hover:opacity-90 transition-opacity border-none cursor-pointer">
                Enable
              </button>
            </div>
            <div className="flex justify-between items-center py-2 border-t border-outline">
              <div>
                <p className="font-body font-medium text-sm text-on-surface">Active Sessions</p>
                <p className="font-body text-sm text-on-surface-variant">1 device signed in</p>
              </div>
              <button className="px-4 py-2 rounded-full border border-outline text-on-surface font-body font-bold text-sm hover:bg-surface-container transition-colors bg-transparent cursor-pointer">
                Manage
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
